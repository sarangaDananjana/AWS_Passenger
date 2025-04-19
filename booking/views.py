from members.models import NormalUserProfile
from decimal import Decimal
from django.db import transaction
from django.utils.timezone import now
from django.utils.timezone import localtime
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from booking.models import BusTrip, Booking
from busstops.models import Seat, BoardingPoint
from .utils import generate_secure_qr_data
from busstops.utils import calculate_bus_trip_end_time, calculate_rough_arrival_time
from members.models import User
from members.models import Notification


SECRET_QR_KEY = settings.SECRET_KEY  # Use a secret key to sign QR codes


def send_booking_notification(user, bus_trip):
    """
    Sends a notification when the user books a trip.
    """
    Notification.objects.create(
        user=user,
        message=f"Your booking for {bus_trip.bus.bus_name} on {bus_trip.route.name} has been confirmed!",
        notification_type="BOOKING_CONFIRMATION"
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_seat(request):
    """
    API to book seats for a bus trip.
    Requires: trip_id, seat_ids (list), start_point_id, end_point_id, fare_price.
    """
    user = request.user
    trip_id = request.data.get('trip_id')
    seat_ids = request.data.get('seat_ids', [])  # Multiple seats
    start_point_id = request.data.get('start_point_id')
    end_point_id = request.data.get('end_point_id')
    fare_price = request.data.get('fare_price')  # Get fare from frontend JSON

    if not trip_id or not seat_ids or not start_point_id or not end_point_id or fare_price is None:
        return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        bus_trip = BusTrip.objects.get(id=trip_id)
        bus = bus_trip.bus  # Get the bus
        start_point = BoardingPoint.objects.get(id=start_point_id)
        end_point = BoardingPoint.objects.get(id=end_point_id)
    except (BusTrip.DoesNotExist, BoardingPoint.DoesNotExist):
        return Response({"error": "Invalid trip ID or boarding points."}, status=status.HTTP_400_BAD_REQUEST)

    bookings = []

    with transaction.atomic():
        for seat_id in seat_ids:
            try:
                seat = Seat.objects.get(id=seat_id)

                # 🔍 Check if seat is already booked for this trip
                if Booking.objects.filter(bus_trip=bus_trip, seat=seat).exists():
                    return Response({"error": f"Seat {seat_id} is already booked for this trip."}, status=status.HTTP_400_BAD_REQUEST)

                # ✅ Save booking with fare price from frontend
                booking = Booking.objects.create(
                    user=user,
                    bus_trip=bus_trip,
                    seat=seat,
                    # Now using the frontend-provided fare
                    fare_price=fare_price / len(seat_ids) +
                    (fare_price / len(seat_ids)) * 0.04,
                    company_4_precent_cut=(fare_price / len(seat_ids)) * 0.04,
                    start_point=start_point,
                    end_point=end_point
                )

                send_booking_notification(user, bus_trip)

                bus_trip.revenue += Decimal((fare_price / len(seat_ids)) -
                                            (fare_price / len(seat_ids)) * 0.03)
                bus_trip.company_3_percent_cut += Decimal(
                    (fare_price / len(seat_ids)) * 0.03)
                bus_trip.save()

                generate_secure_qr_data(booking)

                bookings.append({
                    "booking_id": booking.id,
                    "seat_id": seat.id,
                    "seat_number": seat.seat_number,
                    "booked_at": localtime(booking.booked_at).strftime("%Y-%m-%d %H:%M:%S"),
                    "fare_price": fare_price/len(seat_ids),
                    "bus_type": bus.bus_type,  # Return bus type
                    "qr_code_url": request.build_absolute_uri(booking.qr_code.url),
                    "message": "Booking confirmed!"
                })

            except Seat.DoesNotExist:
                return Response({"error": f"Seat ID {seat_id} does not exist."}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "message": "Booking successful!",
        "bus_type": bus.bus_type,
        "total_fare": fare_price * len(seat_ids),
        "bookings": bookings
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reschedule_booking(request):
    """
    API to reschedule an existing booking.
    - Updates the old booking with new trip details.
    - Deducts revenue from old trip and adds it to the new trip.
    - Updates `booked_at` to the new reschedule time.
    - Regenerates the QR code.
    - Sets booking_status to 'RESCHEDULED_1'.

    Requires: old_booking (previous booking ID), trip_id, seat_ids, start_point_id, end_point_id, fare_price.
    """
    user = request.user
    old_booking_id = request.data.get('old_booking')
    trip_id = request.data.get('trip_id')
    seat_ids = request.data.get('seat_ids', [])
    start_point_id = request.data.get('start_point_id')
    end_point_id = request.data.get('end_point_id')
    fare_price = request.data.get('fare_price')

    if not old_booking_id or not trip_id or not seat_ids or not start_point_id or not end_point_id or fare_price is None:
        return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 🔍 Fetch the old booking and ensure the user owns it
        booking = Booking.objects.get(id=old_booking_id, user=user)
        old_bus_trip = booking.bus_trip  # Get the old bus trip
    except Booking.DoesNotExist:
        return Response({"error": "Old booking does not exist."}, status=status.HTTP_404_NOT_FOUND)

    try:
        # ✅ Fetch new trip and boarding points
        new_bus_trip = BusTrip.objects.get(id=trip_id)
        start_point = BoardingPoint.objects.get(id=start_point_id)
        end_point = BoardingPoint.objects.get(id=end_point_id)
        # Assuming one seat per booking
        seat = Seat.objects.get(id=seat_ids[0])
    except (BusTrip.DoesNotExist, BoardingPoint.DoesNotExist, Seat.DoesNotExist):
        return Response({"error": "Invalid trip ID, seat, or boarding points."}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        # ✅ Deduct the fare from the old bus trip's revenue
        old_bus_trip.revenue -= booking.fare_price
        old_bus_trip.save()

        # ✅ Add the fare to the new bus trip's revenue
        new_bus_trip.revenue += fare_price
        new_bus_trip.save()

        # ✅ Update the existing booking with new details
        booking.bus_trip = new_bus_trip
        booking.start_point = start_point
        booking.end_point = end_point
        booking.seat = seat
        booking.fare_price = fare_price
        booking.booking_status = "RESCHEDULED_1"
        booking.booked_at = now()  # Update the booked_at time
        booking.save()

        # ✅ Regenerate QR code with updated details
        generate_secure_qr_data(booking)

        return Response({
            "message": "Booking successfully rescheduled!",
            "booking_id": booking.id,
            "old_bus_trip_id": old_bus_trip.id,
            "new_bus_trip_id": new_bus_trip.id,
            "seat_id": seat.id,
            "seat_number": seat.seat_number,
            "start_point": start_point.name,
            "end_point": end_point.name,
            "fare_price": booking.fare_price,
            "booking_status": booking.booking_status,
            "booked_at": localtime(booking.booked_at).strftime("%Y-%m-%d %H:%M:%S"),
            "qr_code_url": request.build_absolute_uri(booking.qr_code.url)
        }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cancel_booking(request, booking_id):

    try:
        # Fetch the booking by ID
        booking = Booking.objects.get(id=booking_id)
        bus_trip = booking.bus_trip  # Get the associated bus trip

        with transaction.atomic():
            # Deduct the fare from the bus trip's revenue
            bus_trip.revenue -= booking.fare_price
            bus_trip.save()

            # Update booking status to 'BOOKING_CANCELED'
            booking.booking_status = "BOOKING_CANCELED"
            booking.save()

        return Response({
            "message": "Booking canceled successfully!"
        }, status=status.HTTP_200_OK)

    except Booking.DoesNotExist:
        return Response({"error": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_booking_history(request):
    """
    Fetch the booking history for the logged-in user.
    Categorized into:
      - Verified Bookings
      - Ongoing Bookings
      - Completed Bookings (Bus trip ended)
    """
    user = request.user
    verified_bookings = []
    ongoing_bookings = []
    completed_bookings = []
    failed_bookings = []

    bookings = Booking.objects.filter(
        user=user).select_related('bus_trip', 'seat')

    for booking in bookings:
        bus_trip = booking.bus_trip
        bus_trip_end_time = calculate_bus_trip_end_time(bus_trip)
        route_sections = bus_trip.route.sections.order_by('position')
        start_point_arrival_time = calculate_rough_arrival_time(
            bus_trip.start_time, route_sections, booking.start_point.name)
        end_point_arrival_time = calculate_rough_arrival_time(
            bus_trip.start_time, route_sections, booking.end_point.name)

        booking_data = {
            "booking_id": booking.id,
            "bus_trip_id": bus_trip.id,
            "bus_trip_name": bus_trip.name,
            "seat_number": booking.seat.seat_number,
            "start_point": booking.start_point.name,
            "start_point_id": booking.start_point.id,
            "start_point_arrival_time": localtime(start_point_arrival_time).strftime("%Y-%m-%d %H:%M:%S"),
            "end_point_arrival_time": localtime(end_point_arrival_time).strftime("%Y-%m-%d %H:%M:%S"),
            "end_point": booking.end_point.name,
            "end_point_id": booking.end_point.id,
            "fare_price": booking.fare_price,
            "booked_at": localtime(booking.booked_at).strftime("%Y-%m-%d %H:%M:%S"),
            "qr_code_url": request.build_absolute_uri(booking.qr_code.url) if booking.qr_code else None,
            "bus_trip_start_time": localtime(bus_trip.start_time).strftime("%Y-%m-%d %H:%M:%S"),
            "bus_trip_end_time": localtime(bus_trip_end_time).strftime("%Y-%m-%d %H:%M:%S"),
            "booking_status": booking.booking_status,
            "is_bus_trip_canceled": bus_trip.is_bustrip_canceled
        }

        if booking.booking_status == "VERIFIED" and now() >= bus_trip_end_time:
            completed_bookings.append(booking_data)
        elif not booking.booking_status == "VERIFIED" and now() >= bus_trip_end_time:
            failed_bookings.append(booking_data)
        elif booking.booking_status == "VERIFIED":
            verified_bookings.append(booking_data)
        elif now() < bus_trip_end_time:
            ongoing_bookings.append(booking_data)

    return Response({
        "verified_bookings": verified_bookings,
        "ongoing_bookings": ongoing_bookings,
        "completed_bookings": completed_bookings,
        "failed_bookings": failed_bookings
    }, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def home_ongoing_bookings(request):
    """
    Fetch only the ongoing bookings for the logged-in user.
    If a user has multiple seats booked for the same trip, group them into one entry.
    """
    user = request.user
    grouped_bookings = {}

    bookings = Booking.objects.filter(
        user=user, booking_status__in=["BOOKED", "RESCHEDULED_1"]
    ).select_related('bus_trip', 'seat')

    for booking in bookings:
        bus_trip = booking.bus_trip
        bus_trip_end_time = calculate_bus_trip_end_time(bus_trip)

        # Only include bookings where the trip is still ongoing
        if now() < bus_trip_end_time:
            route_sections = bus_trip.route.sections.order_by('position')
            start_point_arrival_time = calculate_rough_arrival_time(
                bus_trip.start_time, route_sections, booking.start_point.name
            )

            # If this trip is already in the dictionary, add the seat to the list
            if bus_trip.id in grouped_bookings:
                grouped_bookings[bus_trip.id]["booked_seats"].append({
                    "seat_number": booking.seat.seat_number
                })
            else:
                # First time adding this trip → Create a new entry
                grouped_bookings[bus_trip.id] = {
                    "bus_trip_id": bus_trip.id,
                    "bus_trip_name": bus_trip.name,
                    "bus_name": bus_trip.bus.bus_name,
                    "bus_number": bus_trip.bus.bus_number,
                    "start_point": booking.start_point.name,
                    "start_point_arrival_time": localtime(start_point_arrival_time).strftime("%Y-%m-%d %H:%M:%S"),
                    "end_point": booking.end_point.name,
                    "bus_trip_start_time": localtime(bus_trip.start_time).strftime("%Y-%m-%d %H:%M:%S"),
                    "bus_trip_end_time": localtime(bus_trip_end_time).strftime("%Y-%m-%d %H:%M:%S"),
                    "booking_status": booking.booking_status,
                    "booked_seats": [{
                        "seat_number": booking.seat.seat_number
                    }]
                }

    return Response({
        "ongoing_bookings": list(grouped_bookings.values())
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """
    Get all notifications for the logged-in user.
    """
    user = request.user
    notifications = Notification.objects.filter(
        user=user).order_by('-created_at')

    return Response({
        "notifications": [
            {
                "id": notif.id,
                "message": notif.message,
                "type": notif.notification_type,
                "created_at": localtime(notif.created_at).strftime("%Y-%m-%d %H:%M:%S"),
                "is_read": notif.is_read
            } for notif in notifications
        ]
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notifications_as_read(request):
    """
    Mark notifications as read.
    """
    user = request.user
    notification_id = request.data.get('id')
    if not notification_id:
        return Response({"error": "Notification ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    updated_count = Notification.objects.filter(
        user=user, id=notification_id, is_read=False
    ).update(is_read=True)

    if updated_count == 0:
        return Response({"error": "Notification not found or already read"}, status=status.HTTP_404_NOT_FOUND)

    return Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ticket_details(request, booking_id):
    """
    Fetch details of a specific ticket by booking ID.
    """
    user = request.user

    try:
        booking = Booking.objects.select_related(
            'bus_trip', 'seat').get(id=booking_id, user=user)
    except Booking.DoesNotExist:
        return Response({"error": "Booking not found or does not belong to this user."}, status=status.HTTP_404_NOT_FOUND)

    bus_trip = booking.bus_trip
    bus_trip_end_time = calculate_bus_trip_end_time(bus_trip)
    route_sections = bus_trip.route.sections.order_by('position')

    start_point_arrival_time = calculate_rough_arrival_time(
        bus_trip.start_time, route_sections, booking.start_point.name
    )

    ticket_data = {
        "booking_id": booking.id,
        "bus_trip_id": bus_trip.id,
        "bus_trip_name": bus_trip.name,
        "route_name": bus_trip.route.name,
        "bus_name": bus_trip.bus.bus_name,
        "bus_number": bus_trip.bus.bus_number,
        "seat_number": booking.seat.seat_number,
        "start_point": booking.start_point.name,
        "start_point_province": booking.start_point.province,
        "start_point_arrival_time": localtime(start_point_arrival_time).strftime("%Y-%m-%d %H:%M:%S"),
        "end_point": booking.end_point.name,
        "end_point_province": booking.end_point.province,
        "fare_price": booking.fare_price,
        "booked_at": localtime(booking.booked_at).strftime("%Y-%m-%d %H:%M:%S"),
        "qr_code_url": request.build_absolute_uri(booking.qr_code.url) if booking.qr_code else None,
        "bus_trip_start_date": localtime(bus_trip.start_time).strftime("%Y-%m-%d"),
        "bus_trip_start_time": localtime(bus_trip.start_time).strftime("%H:%M:%S"),
        "bus_trip_end_date": localtime(bus_trip_end_time).strftime("%Y-%m-%d"),
        "bus_trip_end_time": localtime(bus_trip_end_time).strftime("%H:%M:%S"),
        "user": user.username,
        "user_first_name": user.first_name,
        "user_last_name": user.last_name,
        "booking_status": booking.booking_status
    }

    return Response(ticket_data, status=status.HTTP_200_OK)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_customer_id(request):
    """
    GET: Retrieve the current customer_id of the logged-in Normal User.
    PATCH: Update the customer_id of the logged-in Normal User.
    """
    user = request.user

    # Ensure the user is a Normal User
    if user.role != user.Role.NORMAL_USER:
        return Response({"error": "Only normal users can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    try:
        profile = NormalUserProfile.objects.get(user=user)
    except NormalUserProfile.DoesNotExist:
        return Response({"error": "NormalUserProfile not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response({"customer_id": profile.customer_id}, status=status.HTTP_200_OK)

    elif request.method == "PATCH":
        customer_id = request.data.get("customer_id")
        if not customer_id:
            return Response({"error": "customer_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        profile.customer_id = customer_id
        profile.save()

        return Response({
            "message": "customer_id updated successfully",
            "customer_id": profile.customer_id
        }, status=status.HTTP_200_OK)

