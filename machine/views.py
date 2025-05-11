from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from busstops.models import Buses
from members.models import BusConductorProfile, User
from django.shortcuts import get_object_or_404
from busstops.models import BusRoute

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from busstops.models import Buses
from members.models import BusConductorProfile, User

@api_view(['POST'])
def login_conductor(request):
    """
    Log in a bus conductor by bus number alone.
    """
    bus_number = request.data.get('bus_number')
    if not bus_number:
        return Response({"error": "Bus number is required."},
                        status=status.HTTP_400_BAD_REQUEST)

    # 1. Find the bus
    bus = Buses.objects.filter(bus_number=bus_number).first()
    if not bus:
        return Response({"error": "Invalid bus number."},
                        status=status.HTTP_400_BAD_REQUEST)

    # 2. Ensure the owner is a conductor
    user = bus.owner
    if not user or user.role != User.Role.BUS_CONDUCTOR:
        return Response({"error": "No bus-conductor account for this bus."},
                        status=status.HTTP_403_FORBIDDEN)

    # 3. Verify the 'machine' flag
    try:
        profile = BusConductorProfile.objects.get(user=user)
    except BusConductorProfile.DoesNotExist:
        return Response({"error": "Bus conductor profile not found."},
                        status=status.HTTP_404_NOT_FOUND)

    if not profile.machine:
        return Response({"error": "Conductor's machine flag is False."},
                        status=status.HTTP_400_BAD_REQUEST)

    # 4. Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    return Response({
        "message": "Login successful!",
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def route_sections(request, route_id):
    """
    GET /api/routes/<route_id>/
    Returns each section’s name, position, distance, time,
    and just the boarding-point names.
    """
    route = get_object_or_404(BusRoute, pk=route_id)

    sections_data = []
    for sec in route.sections.all().order_by('position'):
        bp_names = [bp.name for bp in sec.section_boarding_points.all()]
        sections_data.append({
            "name":            sec.name,
            "position":        sec.position,
            "distance":        str(sec.distance) if sec.distance is not None else None,
            "time":            str(sec.time)     if sec.time     is not None else None,
            "boarding_points": bp_names,
        })

    return Response({
        "route_id":   route.id,
        "route_name": route.name,
        "sections":   sections_data
    }, status=status.HTTP_200_OK)
