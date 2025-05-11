from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from busstops.models import Buses
from members.models import BusConductorProfile, User
from django.contrib.auth import get_user_model

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
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
