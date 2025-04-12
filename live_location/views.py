from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import LiveLocation
from busstops.models import Buses


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_live_location(request):
    """
    API for bus conductors to update their assigned bus's live location.
    """
    user = request.user

    # Ensure the user is a bus conductor
    if user.role != user.Role.BUS_CONDUCTOR:
        return Response({"error": "Only bus conductors can update live locations."}, status=status.HTTP_403_FORBIDDEN)

    # Ensure the conductor has an assigned bus
    bus = getattr(user, 'bus', None)
    if not bus:
        return Response({"error": "No bus assigned to this conductor."}, status=status.HTTP_400_BAD_REQUEST)

    latitude = request.data.get("latitude")
    longitude = request.data.get("longitude")

    if latitude is None or longitude is None:
        return Response({"error": "Latitude and Longitude are required."}, status=status.HTTP_400_BAD_REQUEST)

    # ✅ Update or create the bus location
    LiveLocation.objects.update_or_create(
        bus=bus,
        defaults={"latitude": latitude, "longitude": longitude}
    )

    return Response({"message": "Live location updated successfully!"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_live_location(request, bus_id):
    """
    API for users to get the live location of a specific bus.
    """
    try:
        live_location = LiveLocation.objects.get(bus_id=bus_id)
        return Response({
            "bus_id": live_location.bus.id,
            "bus_name": live_location.bus.bus_name,
            "latitude": live_location.latitude,
            "longitude": live_location.longitude,
            "last_updated": live_location.last_updated.strftime("%Y-%m-%d %H:%M:%S")
        }, status=status.HTTP_200_OK)

    except LiveLocation.DoesNotExist:
        return Response({"error": "No live location available for this bus."}, status=status.HTTP_404_NOT_FOUND)
