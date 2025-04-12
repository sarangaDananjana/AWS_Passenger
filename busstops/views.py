from datetime import timedelta
import time
from django.shortcuts import render
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils import bus_booking_search, get_available_seats_for_booking, calculate_rough_arrival_time, calculate_total_distance, get_booking_information
from .utils import bus_instant_booking_search, get_available_seats_for_instant_booking, calculate_luxury_bus_fare, calculate_semi_luxury_bus_fare
from .models import BoardingPoint


def home(request):
    return render(request, 'index.html')


def get_suggestions(request):

    term = request.GET.get('term', '')
    if term:
        results = BoardingPoint.objects.filter(name__icontains=term)[:10]
        suggestions = [{"id": bp.id, "name": bp.name,
                        "city": bp.city, "province": bp.province} for bp in results]
        return JsonResponse(suggestions, safe=False)
    return JsonResponse([], safe=False)


@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def booking_search(request):
    # Step 1: Get start and end points from the request
    start_point_id = request.GET.get('start_point')
    end_point_id = request.GET.get('end_point')

    if not start_point_id or not end_point_id:
        return Response({"error": "start_point and end_point are required."}, status=400)

    cache_key = f"booking_search_{start_point_id}_{end_point_id}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data, status=200)

    try:
        # Step 2: Fetch start and end BoardingPoint objects
        start_point = BoardingPoint.objects.get(id=start_point_id)
        end_point = BoardingPoint.objects.get(id=end_point_id)
    except BoardingPoint.DoesNotExist:
        return Response({"error": "Invalid start_point or end_point."}, status=404)

    # Step 3: Get the list of BusTrips
    bookable_trips = bus_booking_search(start_point, end_point)

    # Step 4: Get available seats for each BusTrip
    available_seats = get_available_seats_for_booking(
        bookable_trips)

    # Step 5: Prepare the response data
    trips_data = []
    for trip in bookable_trips:
        bus = trip.bus
        route_sections = trip.route.sections.order_by('position')

        start_section = route_sections.filter(
            section_boarding_points=start_point).first()
        end_section = route_sections.filter(
            section_boarding_points=end_point).first()

        is_start_time_ok = trip.start_time - timedelta(minutes=30)

        fare_info = {"fare_price": 0}

        if bus.bus_type == 'LUXURY':
            fare_info = calculate_luxury_bus_fare(trip.id)
        elif bus.bus_type == 'SEMI_LUXURY':
            fare_info = calculate_semi_luxury_bus_fare(
                trip.id)  # Function should be implemented

            # fare_price = fare_info["fare_price"] if fare_info and "fare_price" in fare_info else 0

        start_arrival_time = calculate_rough_arrival_time(
            trip.start_time, route_sections, start_section)
        end_arrival_time = calculate_rough_arrival_time(
            trip.start_time, route_sections, end_section)

        total_distance = calculate_total_distance(
            route_sections, start_section, end_section)

        trips_data.append({
            "bus_trip_id": trip.id,
            "bus_trip_name": trip.name,
            "available_seats": len(available_seats.get(trip.id, [])),
            "fare_price": fare_info,
            "bus_details": {
                "bus_name": bus.bus_name,
                "bus_number": bus.bus_number
            },
            "start_arrival_time": start_arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_arrival_time": end_arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
            # Ensure the distance is JSON serializable
            "total_distance": float(total_distance),
            "start_point_name": start_point.name,
            "end_point_name": end_point.name,
            "is_start_time_ok": is_start_time_ok.strftime("%Y-%m-%d %H:%M:%S"),
        })

        cache.set(cache_key, trips_data)

    # Step 6: Return the data as JSON response
    time.sleep(1)
    return Response(trips_data, status=200)


@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def instant_booking_search(request):

    start_point_id = request.GET.get('start_point')
    end_point_id = request.GET.get('end_point')

    if not start_point_id or not end_point_id:
        return Response({"error": "start_point and end_point are required."}, status=400)

    try:
        # Step 2: Fetch start and end BoardingPoint objects
        start_point = BoardingPoint.objects.get(id=start_point_id)
        end_point = BoardingPoint.objects.get(id=end_point_id)
    except BoardingPoint.DoesNotExist:
        return Response({"error": "Invalid start_point or end_point."}, status=404)

    bookable_trips = bus_instant_booking_search(start_point, end_point)

    available_seats = get_available_seats_for_instant_booking(
        bookable_trips, start_point, end_point)

    trips_data = []
    for trip in bookable_trips:
        bus = trip.bus
        route_sections = trip.route.sections.all()

        start_section = route_sections.filter(
            section_boarding_points=start_point).first()
        end_section = route_sections.filter(
            section_boarding_points=end_point).first()

        start_arrival_time = calculate_rough_arrival_time(
            trip.start_time, route_sections, start_section)
        end_arrival_time = calculate_rough_arrival_time(
            trip.start_time, route_sections, end_section)

        total_distance = calculate_total_distance(
            route_sections, start_section, end_section)

        trips_data.append({
            "bus_trip_id": trip.id,
            "bus_trip_name": trip.name,
            "available_seats": len(available_seats.get(trip.id, [])),
            "bus_details": {
                "bus_name": bus.bus_name,
                "bus_number": bus.bus_number
            },
            "start_arrival_time": start_arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_arrival_time": end_arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
            # Ensure the distance is JSON serializable
            "total_distance": float(total_distance),
        })

    # Step 6: Return the data as JSON response
    return Response(trips_data, status=200)


@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def fetch_booking_details(request):
    """
    API view to fetch seat details (available, non-available, and seat type)
    for a given bus trip ID.
    """
    bus_trip_id = request.GET.get('bus_trip_id')
    seat_details = get_booking_information(bus_trip_id)

    # Check if an error occurred in the utility function
    if "error" in seat_details:
        return JsonResponse(seat_details, status=404)

    return Response(seat_details, status=200)
