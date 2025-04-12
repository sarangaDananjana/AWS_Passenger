from datetime import timedelta, time
from django.utils.timezone import now
from booking.models import BusTrip, Booking
from .models import BusRoute
from .models import BusFareLuxury, BusFareSemiLuxury


def bus_booking_search(start_point, end_point):

    both_start_and_end_included_routes = BusRoute.objects.filter(
        route_boarding_points=start_point).filter(route_boarding_points=end_point)

    matched_routes = []
    for route in both_start_and_end_included_routes:
        sections = route.sections.all()

        start_section = sections.filter(
            section_boarding_points=start_point).first()
        end_section = sections.filter(
            section_boarding_points=end_point).first()

        if start_section and end_section:
            # Ensure the position of the start section is less than the end section
            if start_section.position < end_section.position:
                matched_routes.append(route)

    current_time = now()

    soon_or_started_trips = BusTrip.objects.filter(
        start_time__lte=current_time + timedelta(minutes=30)
    )

    bookable_trips = BusTrip.objects.exclude(
        id__in=soon_or_started_trips.values_list('id', flat=True)
    )

    bookable_trips_for_user = bookable_trips.filter(route__in=matched_routes)

    return bookable_trips_for_user


def bus_instant_booking_search(start_point, end_point):

    both_start_and_end_included_routes = BusRoute.objects.filter(
        route_boarding_points=start_point).filter(route_boarding_points=end_point)

    matched_routes = []
    for route in both_start_and_end_included_routes:
        sections = route.sections.all()

        start_section = sections.filter(
            section_boarding_points=start_point).first()
        end_section = sections.filter(
            section_boarding_points=end_point).first()

        if start_section and end_section:
            # Ensure the position of the start section is less than the end section
            if start_section.position < end_section.position:
                matched_routes.append(route)

    current_time = now()

    started_trips = BusTrip.objects.filter(
        start_time__gte=current_time)

    bookable_trips = BusTrip.objects.exclude(
        id__in=started_trips.values_list('id', flat=True)
    )

    bookable_trips_for_user = bookable_trips.filter(route__in=matched_routes)

    return bookable_trips_for_user


def get_available_seats_for_instant_booking(bookable_trips_for_user, start_point, end_point):

    available_seats = {}
 # checking the trip one by one in a for loop
    for trip in bookable_trips_for_user:
        # get all the seats of the current checking trip
        all_seats = trip.bus.seats.all()
        # get all the bookings of the current checking trip
        bookings = Booking.objects.filter(bus_trip=trip)

        # get all the sections of the current checking trip
        sections = trip.route.sections.all()

        # get the user's start section of the current checking trip
        user_start_section = sections.filter(
            section_boarding_points=start_point).first()

        # get the user's end section of the current checking trip
        user_end_section = sections.filter(
            section_boarding_points=end_point).first()

        # get the user's inputed start and end section's position numbers
        user_start_pos = user_start_section.position
        user_end_pos = user_end_section.position

        # Step 4: Check availability for each seat
        trip_available_seats = []

        # run a for loop to check all the seats in the current trip
        for seat in all_seats:
            # Check if the seat is unbooked
            seat_bookings = bookings.filter(seat=seat)
            if not seat_bookings.exists():
                trip_available_seats.append(seat)
                continue

            is_available = True
            for booking in seat_bookings:
                # Get section positions for this booking
                booking_start_section = sections.filter(
                    section_boarding_points=booking.start_point).first()
                booking_end_section = sections.filter(
                    section_boarding_points=booking.end_point).first()

                booking_start_pos = booking_start_section.position
                booking_end_pos = booking_end_section.position

                if not (user_end_pos <= booking_start_pos or user_start_pos >= booking_end_pos):
                    is_available = False
                    break

            if is_available:
                trip_available_seats.append(seat)

        available_seats[trip.id] = trip_available_seats

    return available_seats


def get_available_seats_for_booking(bookable_trips_for_user):

    available_seat_count = {}

    for trip in bookable_trips_for_user:
        # Get all seats of the bus associated with this trip
        all_seats = trip.bus.seats.all()

        # Get all bookings for this specific trip
        bookings = Booking.objects.filter(bus_trip=trip)

        # Calculate available seats
        available_seats = [
            seat for seat in all_seats if not bookings.filter(seat=seat).exists()
        ]
        # Store the available seat count for the current trip
        available_seat_count[trip.id] = available_seats

    return available_seat_count


# ✅ Define Global Busy Time Ranges
BUSY_TIME_RANGES = [
    (time(7, 0), time(9, 0)),   # Office morning rush
    (time(13, 30), time(14, 30)),  # School closing
    (time(16, 30), time(19, 30))  # Office evening rush
]


def is_global_busy_time(estimated_time):
    """
    Checks if the estimated time falls within any of the global busy time ranges.
    """
    current_time = estimated_time.time()
    for busy_start, busy_end in BUSY_TIME_RANGES:
        if busy_start <= current_time <= busy_end:
            return True
    return False


def calculate_rough_arrival_time(bus_trip_start_time, sections, target_section):
    """
    Calculate the approximate time a bus will arrive at a specific section,
    applying busy time adjustments dynamically.
    """
    elapsed_time = timedelta()  # Start with 0 elapsed time

    for section in sections:
        if section == target_section:
            break

        if section.time:
            estimated_time_at_section = bus_trip_start_time + elapsed_time

            # ✅ Check if the bus will pass during a global busy time
            if is_global_busy_time(estimated_time_at_section) and section.busy_time:
                elapsed_time += section.busy_time  # Use busy time delay
            else:
                elapsed_time += section.time  # Use normal travel time

    return bus_trip_start_time + elapsed_time


'''
def calculate_rough_arrival_time(bus_trip_start_time, sections, target_section):
    """
    Calculate the approximate time a bus will arrive at a specific section.
    """
    elapsed_time = timedelta()  # Initialize elapsed time
    for section in sections:
        if section == target_section:
            break
        if section.time:
            elapsed_time += section.time

    return bus_trip_start_time + elapsed_time
'''


def calculate_total_distance(sections, start_section, end_section):
    """
    Calculate the total distance between the start and end sections.
    """
    total_distance = 0
    start_counting = False
    for section in sections:
        if section == start_section:
            start_counting = True
        if start_counting and section.distance:
            total_distance += section.distance
        if section == end_section:
            break

    return total_distance


def calculate_luxury_bus_fare(bus_trip_id):
    """
    Calculate fare for a luxury bus trip.

    Steps:
    1. Get the route used by the bus trip.
    2. Find the maximum section position in that route.
    3. Use (max_position - 0) as fare_number.
    4. Fetch fare price from BusFareLuxury.
    """
    try:
        # Fetch the bus trip and its route
        bus_trip = BusTrip.objects.get(id=bus_trip_id)
        route = bus_trip.route

        # Get the max position from sections in the route
        max_section = route.sections.order_by('-position').first()

        if not max_section:
            return {"error": "No sections found for this route."}

        fare_number = max_section.position  # Since start is always 0

        # Get fare price based on fare number
        try:
            fare = BusFareLuxury.objects.get(fare_number=fare_number)
            return {"fare_number": fare_number, "fare_price": fare.fare_price}
        except BusFareLuxury.DoesNotExist:
            return {"error": f"No fare price found for fare number {fare_number}."}

    except BusTrip.DoesNotExist:
        return {"error": "Bus trip not found."}


def calculate_semi_luxury_bus_fare(bus_trip_id):
    """Calculate fare for a semi-luxury bus trip."""
    bus_trip = BusTrip.objects.get(id=bus_trip_id)
    route = bus_trip.route
    max_section = route.sections.order_by('-position').first()

    if not max_section:
        return {"error": "No sections found for this route."}

    fare_number = max_section.position

    try:
        fare = BusFareSemiLuxury.objects.get(fare_number=fare_number)
        return {"fare_number": fare_number, "fare_price": fare.fare_price}
    except BusFareSemiLuxury.DoesNotExist:
        return {"error": f"No fare price found for fare number {fare_number}."}


def get_booking_information(bus_trip_id):
    """
    Utility function to get seat availability information for a specific bus trip.
    Returns a dictionary where seat IDs are mapped to "Available" or "Not-Available".
    """
    try:
        # Fetch the BusTrip instance
        bus_trip = BusTrip.objects.get(id=bus_trip_id)
        bus = bus_trip.bus

        # Get all seats of the bus
        all_seats = bus.seats.all()

        # Fetch bookings for the specific BusTrip
        bookings = Booking.objects.filter(bus_trip=bus_trip)

        # Calculate fare per seat
        fee_per_seat = calculate_luxury_bus_fare(bus_trip_id)

        # Create a seat availability dictionary
        seat_availability = {}

        for seat in all_seats:
            is_booked = bookings.filter(seat=seat).exists()
            seat_availability[seat.id] = "Not-Available" if is_booked else "Available"

        # Return seat details
        return {
            "bus_trip_id": bus_trip_id,
            "bus_trip_name": bus_trip.name,
            "fee_per_seat": fee_per_seat,
            "seat_type": f"{bus.seat_count}-seater",
            "seat_availability": seat_availability  # New format
        }

    except BusTrip.DoesNotExist:
        return {"error": "BusTrip not found."}


def get_booking_info_with_SPandEP(bus_trip_id):
    """
    Retrieve seat availability details for a specific bus trip.
    Includes:
    - Seat ID
    - Availability (Available/Not Available)
    - Start Point (if booked)
    - End Point (if booked)

    Args:
        bus_trip_id (int): The ID of the bus trip.

    Returns:
        dict: A dictionary containing bus trip details with seat booking info.
    """
    try:
        # Fetch the bus trip
        bus_trip = BusTrip.objects.get(id=bus_trip_id)
        bus = bus_trip.bus

        # Get all seats for the bus
        all_seats = bus.seats.all()

        # Fetch all bookings for this bus trip
        bookings = Booking.objects.filter(bus_trip=bus_trip)

        # Prepare seat availability details
        seat_availability = {}

        for seat in all_seats:
            # Check if the seat is booked
            booking = bookings.filter(seat=seat).first()
            if booking:
                seat_availability[seat.id] = {
                    "seat_number": seat.seat_number,
                    "availability": "Not Available",
                    "start_point": booking.start_point.name,  # Retrieve start point name
                    "end_point": booking.end_point.name  # Retrieve end point name
                }
            else:
                seat_availability[seat.id] = {
                    "seat_number": seat.seat_number,
                    "availability": "Available",
                    "start_point": None,
                    "end_point": None
                }

        return {
            "bus_trip_id": bus_trip_id,
            "bus_trip_name": bus_trip.name,
            "seat_type": f"{bus.seat_count}-seater",
            "seat_availability": seat_availability
        }

    except BusTrip.DoesNotExist:
        return {"error": "Bus trip not found."}


def calculate_bus_trip_end_time(bus_trip):
    """
    Calculates the end time of a bus trip by summing all section durations.
    """
    sections = bus_trip.route.sections.all()
    total_duration = timedelta()  # Initialize time sum

    for section in sections:
        if section.time:  # Ensure section has a duration
            total_duration += section.time

    return bus_trip.start_time + total_duration
