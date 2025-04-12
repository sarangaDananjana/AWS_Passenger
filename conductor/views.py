from datetime import timedelta
import hmac
import hashlib
import base64
from django.utils.timezone import now
from django.conf import settings
from django.utils.timezone import localtime
from django.db import models
from django.http import JsonResponse
from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from busstops.models import BusRoute
from busstops.utils import calculate_bus_trip_end_time, get_booking_info_with_SPandEP
from booking.models import BusTrip, Booking
from members.models import User
from .models import ConAppVersion

SECRET_QR_KEY = settings.SECRET_KEY


@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def add_bus_trip(request):
    """
    Bus conductors can add a trip for their assigned bus.
    """
    user = request.user

    # Ensure user is a bus conductor
    if user.role != User.Role.BUS_CONDUCTOR:
        return Response({"error": "Only bus conductors can add bus trips."}, status=status.HTTP_403_FORBIDDEN)

    # Get the bus assigned to the conductor
    bus = getattr(user, 'bus', None)
    if not bus:
        return Response({"error": "No bus assigned to this conductor."}, status=status.HTTP_400_BAD_REQUEST)

    route_id = request.data.get("route_id")
    start_time = request.data.get("start_time")

    if not route_id or not start_time:
        return Response({"error": "Route ID and Start Time are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        bus_trip = BusTrip.objects.create(
            bus=bus,
            route_id=route_id,
            start_time=start_time
        )
        return Response({
            "message": "Bus trip added successfully!",
            "bus_trip_id": bus_trip.id,
            "bus_name": bus.bus_name,
            "route_id": route_id,
            "start_time": start_time
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def view_bus_trip_details(request, trip_id):
    """
    Fetch all details of a specific bus trip.
    Returns total revenue, booked seats, and revenue status.
    """
    user = request.user

    if user.role != User.Role.BUS_CONDUCTOR:
        return Response({"error": "Only bus conductors can access this."}, status=status.HTTP_403_FORBIDDEN)

    bus = getattr(user, 'bus', None)
    if not bus:
        return Response({"error": "No bus assigned to this conductor."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get the bus trip assigned to this conductor's bus
        bus_trip = BusTrip.objects.get(id=trip_id, bus=bus)
        bookings = Booking.objects.filter(bus_trip=bus_trip)

        # 🚍 Get booked seat details
        seat_data = [{
            "booking_id": booking.id,
            "seat_number": booking.seat.seat_number,
            "start_point": booking.start_point.name,
            "end_point": booking.end_point.name,
            "fare_price": booking.fare_price,
            "booked_at": localtime(booking.booked_at).strftime("%Y-%m-%d %H:%M:%S"),
            "booking_status": booking.booking_status
        } for booking in bookings]

        return Response({
            "bus_trip_id": trip_id,
            "bus_name": bus_trip.bus.bus_name,
            "route_name": bus_trip.route.name,
            "start_time": localtime(bus_trip.start_time).strftime("%Y-%m-%d %H:%M:%S"),
            "total_revenue": bus_trip.revenue,
            "is_revenue_released": bus_trip.is_revenue_released,  # ✅ New field
            "booked_seats": seat_data
        }, status=status.HTTP_200_OK)

    except BusTrip.DoesNotExist:
        return Response({"error": "Bus trip not found or not assigned to this conductor."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def search_bus_routes(request):
    """
    Get all available bus routes or filter by search query (name or route number).
    """
    query = request.GET.get("query", "").strip(
    )  # Get search query from request

    if query:
        # Search by route name or route number (case-insensitive)
        routes = BusRoute.objects.filter(
            models.Q(name__icontains=query) | models.Q(
                route_number__icontains=query)
        ).values("id", "name", "route_number")
    else:
        # Return all routes if no query is provided
        routes = BusRoute.objects.all().values("id", "name", "route_number")

    return Response({"routes": list(routes)}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_revenue_report(request):
    """
    Get the revenue report for the currently logged-in bus conductor user.
    Includes revenue from trips, total trips for the week, and booking history for the last 7 days.
    """
    user = request.user
    if user.role != User.Role.BUS_CONDUCTOR:
        return Response({"error": "Only bus conductors can access this report."}, status=status.HTTP_403_FORBIDDEN)

    # 1. Get the bus assigned to the logged-in bus conductor
    bus = user.bus

    if not bus:
        return Response({"error": "Bus conductor is not assigned a bus."}, status=status.HTTP_400_BAD_REQUEST)

    # 2. Calculate the revenue for trips where revenue is not released.
    unreleased_revenue = BusTrip.objects.filter(
        bus=bus, is_revenue_released=False
    ).aggregate(total_revenue=Sum('revenue'))['total_revenue'] or 0.0

    # 3. Total trips for the current week (starting from Monday)
    start_of_week = now() - timedelta(days=now().weekday()
                                      )  # Start of this week (Monday)
    # End of this week (Sunday)
    end_of_week = start_of_week + timedelta(days=7)

    total_trips_this_week = BusTrip.objects.filter(
        bus=bus, 
        start_time__range=[start_of_week, end_of_week],
        is_bustrip_canceled=False
    ).count()

    last_5_bookings = Booking.objects.filter(
        bus_trip__bus=bus).order_by('-booked_at')[:5]

    booking_data = [{
        "bus_trip_name": booking.bus_trip.name,
        "start_point": booking.start_point.name,
        "end_point": booking.end_point.name,
        "seat_number": booking.seat.seat_number,
        "fare_price": booking.fare_price
    } for booking in last_5_bookings]

    # 5. Return the response with all the data
    report_data = {
        'bus_number': user.bus.bus_number,
        'unreleased_revenue': unreleased_revenue,
        'total_trips_this_week': total_trips_this_week,
        'last_5_bookings': booking_data
    }

    return Response(report_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_upcoming_trips(request):
    """
    Get the upcoming trips for the currently logged-in bus conductor.
    Filters trips based on the current time (only trips that haven't started yet).
    """
    user = request.user

    if user.role != User.Role.BUS_CONDUCTOR:
        return Response({"error": "Only bus conductors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    # Get the bus assigned to the current bus conductor
    bus = user.bus

    if not bus:
        return Response({"error": "Bus conductor is not assigned to a bus."}, status=status.HTTP_400_BAD_REQUEST)

    # Filter bus trips for the conductor's bus where the trip start time is greater than the current time
    upcoming_trips = BusTrip.objects.filter(
        bus=bus,
        start_time__gt=now()
    ).values('id', 'name', 'start_time', 'is_bustrip_canceled').order_by('start_time')

    # Prepare the response data
    trips_data = [
        {
            "trip_id": trip['id'],
            "trip_name": trip['name'],
            "start_date": localtime(trip['start_time']).strftime("%Y-%m-%d"),
            "start_time": localtime(trip['start_time']).strftime("%H:%M:%S"),
            "is_bustrip_canceled": trip['is_bustrip_canceled']
        }
        for trip in upcoming_trips
    ]

    return Response({
        "upcoming_trips": trips_data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_booking(request):
    """
    Allows bus conductors to scan a booking QR code.
    The booking fee is added to BusTrip revenue.
    """
    user = request.user

    # Ensure the user is a bus conductor
    if user.role != User.Role.BUS_CONDUCTOR:
        return Response({"error": "Only bus conductors can verify tickets."}, status=status.HTTP_403_FORBIDDEN)

    qr_code_data = request.data.get("qr_code_data")  # Expect the QR code data

    if not qr_code_data:
        return Response({"error": "QR Code data is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # ✅ Validate QR code format before splitting
        qr_data_parts = qr_code_data.split("|")
        if len(qr_data_parts) != 4:
            return Response({"error": "Invalid QR code format."}, status=status.HTTP_400_BAD_REQUEST)

        booking_id, user_id, bus_trip_id, received_signature = qr_data_parts

        # ✅ Validate that booking exists
        booking = Booking.objects.get(
            id=booking_id, bus_trip_id=bus_trip_id, user_id=user_id)
        bus_trip = booking.bus_trip  # Get the associated bus trip
        bus = bus_trip.bus  # Get the bus

        # ✅ Ensure bus conductor is assigned to this bus
        if user.bus != bus:
            return Response({"error": "You are not assigned to this bus."}, status=status.HTTP_403_FORBIDDEN)

        # ✅ Prevent multiple verifications
        if booking.booking_status == "VERIFIED":
            return Response({"error": "This booking has already been verified."}, status=status.HTTP_400_BAD_REQUEST)

        # 🔒 Secure validation: Recalculate signature
        expected_payload = f"{booking.id}|{booking.user.id}|{booking.bus_trip.id}"
        expected_signature = hmac.new(
            SECRET_QR_KEY.encode(), expected_payload.encode(), hashlib.sha256
        ).digest()
        expected_signature = base64.urlsafe_b64encode(
            expected_signature).decode()

        # ✅ Compare received and expected signatures
        if not hmac.compare_digest(expected_signature, received_signature):
            return Response({"error": "QR Code is tampered or invalid."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Verify the booking
        booking.booking_status = "VERIFIED"
        booking.save()

        return Response({
            "message": "Booking verified successfully!",
            "bus_trip_id": bus_trip.id,
            "new_revenue": bus_trip.revenue
        }, status=status.HTTP_200_OK)

    except Booking.DoesNotExist:
        return Response({"error": "Invalid booking data."}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bus_trip_revenue(request):
    """
    Fetch revenue details for each bus trip of the logged-in bus conductor.
    Includes trip name, start time, total revenue, number of reserved seats, and if the revenue is released.
    """
    user = request.user

    # Ensure the user is a bus conductor
    if user.role != User.Role.BUS_CONDUCTOR:
        return Response({"error": "Only bus conductors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    # Get the bus assigned to the logged-in bus conductor
    bus = user.bus

    if not bus:
        return Response({"error": "Bus conductor is not assigned to a bus."}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch all bus trips for this conductor's bus
    bus_trips = BusTrip.objects.filter(bus=bus).values(
        'id', 'name', 'start_time', 'is_revenue_released', 'revenue'
    )

    # Prepare the response data
    trip_data = []
    for trip in bus_trips:
        # Count the number of reserved seats
        reserved_seats = Booking.objects.filter(bus_trip_id=trip['id']).count()

        trip_data.append({
            'bus_trip_name': trip['name'],
            'bus_trip_start_time': localtime(trip['start_time']).strftime("%Y-%m-%d %H:%M:%S"),
            'bus_trip_revenue': trip['revenue'],
            'reserved_seats': reserved_seats,
            'is_revenue_released': trip['is_revenue_released']
        })

    return Response({
        'bus_trip_revenues': trip_data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def fetch_booking_details_for_conductor(request):
    """
    API view to fetch seat details (available, non-available, and seat type)
    for a given bus trip ID.
    """
    bus_trip_id = request.GET.get('bus_trip_id')
    seat_details = get_booking_info_with_SPandEP(bus_trip_id)

    # Check if an error occurred in the utility function
    if "error" in seat_details:
        return Response({"error": "Bus trip not found."}, status=status.HTTP_404_NOT_FOUND)

    return Response(seat_details, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_bus_trip(request, trip_id):
    """
    Cancel a bus trip and update all bookings with 'BUS_TRIP_CANCELED' status.
    """
    try:
        bus_trip = BusTrip.objects.get(id=trip_id)
        bus_trip.is_bustrip_canceled = True
        bus_trip.revenue = 0.0
        bus_trip.save()  # Automatically updates related bookings

        return Response({"message": "Bus trip canceled, and all bookings updated."}, status=status.HTTP_200_OK)

    except BusTrip.DoesNotExist:
        return Response({"error": "Bus trip not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_last_7_trips_with_bookings(request):
    """
    API to fetch the last 7 bus trips for the logged-in bus conductor.
    Includes all bookings for each trip with:
    - Seat Number
    - Start Point
    - End Point
    - Fare Price
    """
    user = request.user

    if user.role != User.Role.BUS_CONDUCTOR:
        return Response({"error": "Only bus conductors can access this report."}, status=status.HTTP_403_FORBIDDEN)

    # Get the bus assigned to the logged-in conductor
    bus = user.bus
    if not bus:
        return Response({"error": "Bus conductor is not assigned to a bus."}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch last 7 bus trips
    last_7_trips = BusTrip.objects.filter(bus=bus).order_by('-start_time')[:7]

    # Prepare trip data
    trip_data = []
    for trip in last_7_trips:
        # Fetch all bookings for this trip
        bookings = Booking.objects.filter(bus_trip=trip).order_by('-booked_at')

        # Format booking details
        booking_data = [{
            "seat_number": booking.seat.seat_number,
            "start_point": booking.start_point.name,
            "end_point": booking.end_point.name,
            "fare_price": booking.fare_price
        } for booking in bookings]

        trip_data.append({
            "bus_trip_name": trip.name,
            "bookings": booking_data
        })

    return Response({"last_7_trips": trip_data}, status=status.HTTP_200_OK)



@api_view(['GET'])
def con_app_check_update(request):
    user_version = request.GET.get('current_app_version', None)

    if not user_version:
        return Response({"error": "Version parameter is required"}, status=400)

    try:
        latest_version = ConAppVersion.objects.latest(
            'created_at')  # Get the newest version
    except ConAppVersion.DoesNotExist:
        return Response({"error": "No version info available"}, status=500)

    update_required = user_version < latest_version.version  # Compare versions

    return Response({
        "update_required": update_required,
        "latest_version": latest_version.version,
        "update_url": latest_version.update_url if update_required else None
    })
