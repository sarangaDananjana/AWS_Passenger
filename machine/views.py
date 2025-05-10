from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from busstops.models import Buses
from members.models import BusConductorProfile, User
from django.contrib.auth import get_user_model

@api_view(['POST'])
def login_conductor(request):
    """
    Log in for Bus Conductor using bus number and validate machine attribute.
    """
    bus_number = request.data.get('bus_number')
    if not bus_number:
        return Response({"error": "Bus number is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Check if bus number exists in the system
    bus = Buses.objects.filter(bus_number=bus_number).first()

    if not bus:
        return Response({"error": "Invalid bus number."}, status=status.HTTP_400_BAD_REQUEST)

    # Get the bus conductor associated with the bus number
    try:
        bus_conductor_profile = BusConductorProfile.objects.get(user=bus.owner)
    except BusConductorProfile.DoesNotExist:
        return Response({"error": "No bus conductor profile found for this bus."}, status=status.HTTP_404_NOT_FOUND)

    # Check if the machine attribute is True
    if bus_conductor_profile.machine:
        # Generate JWT tokens for the bus conductor
        user = bus.owner  # The bus owner's user object
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Return JWT tokens
        return Response({
            "message": "Login successful!",
            "access": access_token,
            "refresh": refresh_token
        }, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Bus conductor profile does not have machine set to True."}, status=status.HTTP_400_BAD_REQUEST)
