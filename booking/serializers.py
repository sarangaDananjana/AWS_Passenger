from rest_framework import serializers
from .models import Booking


class BookingSerializer(serializers.ModelSerializer):

    booked_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Booking
        fields = ['bus_trip', 'seat', 'start_point', 'end_point', 'booked_at']

    def validate(self, data):
        """
        Validate booking request before saving.
        """
        bus_trip = data['bus_trip']
        seat = data['seat']
        start_point = data['start_point']
        end_point = data['end_point']

        # Ensure the seat belongs to the correct bus trip
        if seat.bus != bus_trip.bus:
            raise serializers.ValidationError(
                "This seat does not belong to the selected bus trip.")

        # Ensure the start and end points are in the bus route
        route = bus_trip.route
        if start_point not in route.route_boarding_points.all() or end_point not in route.route_boarding_points.all():
            raise serializers.ValidationError(
                "Invalid start or end point for this route.")

        # Check if the seat is already booked for this trip
        if Booking.objects.filter(bus_trip=bus_trip, seat=seat).exists():
            raise serializers.ValidationError(
                "This seat is already booked for the selected trip.")

        return data
