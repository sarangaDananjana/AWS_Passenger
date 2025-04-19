import requests
from members.models import User, NormalUserProfile
from busstops.models import Buses
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.utils.timezone import now
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import BusConductorDetailsSerializer
from .serializers import UserRegistrationSerializer, BusSerializer
from .models import User, BusConductorProfile, AppVersion
from django.db import transaction


@api_view(['POST'])
def register_or_login_user(request):
    role = request.data.get('role')
    phone_number = request.data.get('phone_number')

    # Validate phone number
    if not phone_number:
        return Response({"error": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Validate role
    if not role or role not in [User.Role.NORMAL_USER, User.Role.BUS_CONDUCTOR]:
        return Response({"error": "Invalid role specified."}, status=status.HTTP_400_BAD_REQUEST)

    # Check if user with phone number exists
    user = User.objects.filter(phone_number=phone_number).first()

    if user:
        # User exists, generate OTP and send it
        user.generate_otp()
        otp_code = user.otp_code
        message = f"Your OTP code is: {otp_code}"

        # Send OTP via SMS (using Text.lk API)
        response = requests.post(
            "https://app.text.lk/api/v3/sms/send",
            headers={
                "Authorization": "Bearer 319|OAWuEVQ24CJPu7oprqZiplNyErfta1oB5aFvhhiU37ced9f0",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json={
                "recipient": user.phone_number,
                "sender_id": "TextLKDemo",
                "type": "plain",
                "message": message
            }
        )

        if response.status_code == 200:
            return Response({"message": "OTP sent successfully! Please verify."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to send OTP via SMS."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    else:
        # User does not exist, create a new user
        user = User.objects.create(phone_number=phone_number, role=role)
        user.save()

        # Generate OTP for the new user
        user.generate_otp()
        otp_code = user.otp_code
        message = f"Your OTP code is: {otp_code}"

        # Send OTP via SMS (using Text.lk API)
        response = requests.post(
            "https://app.text.lk/api/v3/sms/send",
            headers={
                "Authorization": "Bearer 319|OAWuEVQ24CJPu7oprqZiplNyErfta1oB5aFvhhiU37ced9f0",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json={
                "recipient": user.phone_number,
                "sender_id": "TextLKDemo",
                "type": "plain",
                "message": message
            }
        )

        if response.status_code == 200:
            return Response({"message": "OTP sent successfully! Please verify."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": "Failed to send OTP via SMS."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def register_or_login_conductor(request):
    """
    Handles registration and login for bus conductors using phone number and bus number.
    """
    phone_number = request.data.get('phone_number')
    bus_number = request.data.get('bus_number')

    # Validate input
    if not phone_number or not bus_number:
        return Response({"error": "Phone number and bus number are required."}, status=status.HTTP_400_BAD_REQUEST)

    # Check if there's an existing user with this phone number and bus number
    user = User.objects.filter(
        phone_number=phone_number, role=User.Role.BUS_CONDUCTOR).first()
    bus = Buses.objects.filter(bus_number=bus_number).first()

    if user and bus and bus.owner == user:
        # If both phone number and bus number match, send OTP and allow login
        user.generate_otp()
        otp_code = user.otp_code
        message = f"Your OTP code is: {otp_code}"

        # Send OTP via SMS
        response = requests.post(
            "https://app.text.lk/api/v3/sms/send",
            headers={
                "Authorization": "Bearer 319|OAWuEVQ24CJPu7oprqZiplNyErfta1oB5aFvhhiU37ced9f0",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json={
                "recipient": user.phone_number,
                "sender_id": "TextLKDemo",
                "type": "plain",
                "message": message
            }
        )

        if response.status_code == 200:
            return Response({"message": "OTP sent successfully! Please verify."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to send OTP via SMS."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # If either the phone number or bus number exists, but they are not linked
    if bus and not user:
        return Response({"error": "Invalid phone number."}, status=status.HTTP_400_BAD_REQUEST)

    if user and not bus:
        return Response({"error": "Invalid bus number."}, status=status.HTTP_400_BAD_REQUEST)

    if user and bus and bus.owner != user:
        return Response({"error": "Invalid phone number."}, status=status.HTTP_400_BAD_REQUEST)

    # If both phone number and bus number do not exist, create a new user and bus
    with transaction.atomic():
        new_user = User.objects.create(
            phone_number=phone_number,
            role=User.Role.BUS_CONDUCTOR
        )

        new_bus = Buses.objects.create(
            bus_number=bus_number,
            owner=new_user
        )

        # Generate OTP for the new user
        new_user.generate_otp()
        otp_code = new_user.otp_code
        message = f"Your OTP code is: {otp_code}"

        # Send OTP via SMS
        response = requests.post(
            "https://app.text.lk/api/v3/sms/send",
            headers={
                "Authorization": "Bearer 319|OAWuEVQ24CJPu7oprqZiplNyErfta1oB5aFvhhiU37ced9f0",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json={
                "recipient": new_user.phone_number,
                "sender_id": "TextLKDemo",
                "type": "plain",
                "message": message
            }
        )

        if response.status_code == 200:
            return Response({"message": "OTP sent successfully! Please verify."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": "Failed to send OTP via SMS."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def verify_otp(request):
    """
    Verifies the OTP entered by the user and issues JWT on successful authentication.
    """
    phone_number = request.data.get("phone_number")
    otp_code = request.data.get("otp_code")

    try:
        user = User.objects.get(phone_number=phone_number)

        # Check if OTP is valid
        if user.otp_code != otp_code:
            return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if OTP has expired
        if now() > user.otp_expires_at:
            return Response({"error": "OTP expired."}, status=status.HTTP_400_BAD_REQUEST)

        # Mark user as verified
        user.is_verified = True
        user.otp_code = None  # Clear OTP after verification
        user.otp_expires_at = None
        user.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Return JWT tokens
        return Response({
            "message": "OTP verified successfully! User is now active.",
            "access": access_token,
            "refresh": refresh_token
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({"error": "User with this phone number not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def logout_user(request):
    """
    Logout view - Blacklists the refresh token.
    """
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()  # Blacklist the refresh token
        return Response({"message": "Logout successful!"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": f"Invalid token: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_details(request):
    """
    API to show user details and allow users to edit specific fields.
    """
    user = request.user

    if user.role != User.Role.NORMAL_USER:
        return Response({"error": "Only normal users can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        # Safely access the profile_pic field and check if it exists
        profile_pic = user.normaluserprofile.profile_pic if user.normaluserprofile and user.normaluserprofile.profile_pic else None

        user_data = {
            "email": user.email,
            "is_email_verified": user.is_email_verified,
            "phone_number": user.phone_number,
            "gender": user.gender,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "birthday": user.birthday,
            "profile_pic": profile_pic,  # Handle None or missing file gracefully
            "customer_id": user.normaluserprofile.customer_id if user.normaluserprofile else None,
            "lane_1": user.normaluserprofile.lane_1 if user.normaluserprofile else None,
            "lane_2": user.normaluserprofile.lane_2 if user.normaluserprofile else None,
            "city": user.normaluserprofile.city if user.normaluserprofile else None,
            "postal_code": user.normaluserprofile.postal_code if user.normaluserprofile else None,
        }
        return Response(user_data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        new_email = request.data.get("email")
        new_first_name = request.data.get("first_name")
        new_last_name = request.data.get("last_name")
        new_gender = request.data.get("gender")
        new_birthday = request.data.get("birthday")

        if new_email and new_email != user.email:
            user.email = new_email
            user.is_email_verified = False  # Mark email as unverified
            user.generate_email_otp()  # Generate and send OTP for email verification

        # Update other fields, excluding customer_id and phone_number
        user.first_name = new_first_name if new_first_name else user.first_name
        user.last_name = new_last_name if new_last_name else user.last_name
        user.gender = new_gender if new_gender else user.gender
        user.birthday = new_birthday if new_birthday else user.birthday

        # Update profile fields if available
        normal_user_profile = user.normaluserprofile
        if normal_user_profile is None:
            normal_user_profile = NormalUserProfile.objects.create(user=user)

        normal_user_profile.lane_1 = request.data.get(
            "lane_1", normal_user_profile.lane_1)
        normal_user_profile.lane_2 = request.data.get(
            "lane_2", normal_user_profile.lane_2)
        normal_user_profile.city = request.data.get(
            "city", normal_user_profile.city)
        normal_user_profile.postal_code = request.data.get(
            "postal_code", normal_user_profile.postal_code)
        normal_user_profile.save()

        # Save the user with the updated information
        user.save()

        return Response({
            "message": "User details updated successfully!"
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_email_otp(request):
    """
    Verify the email using OTP sent to the user's email.
    """
    otp_code = request.data.get("otp_code")  # OTP from the user

    if not otp_code:
        return Response({"error": "OTP is required."}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user  # The logged-in user

    # Check if the OTP entered by the user matches the stored OTP
    if user.email_otp_code != otp_code:
        return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the OTP has expired
    if now() > user.email_otp_expires_at:
        return Response({"error": "OTP expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

    # Mark the email as verified and clear OTP fields
    user.is_email_verified = True
    user.email_otp_code = None  # Clear the OTP after successful verification
    user.email_otp_expires_at = None  # Clear the expiration time
    user.save()

    return Response({"message": "Email verified successfully!"}, status=status.HTTP_200_OK)


'''
@api_view(['GET', 'PUT'])  # GET to view details, PUT to update profile pic
# Only authenticated users can access this
@permission_classes([IsAuthenticated])
def user_details(request):
    """
    API to show user details and allow profile picture updates.
    """
    user = request.user  # Get the authenticated user

    if user.role != User.Role.NORMAL_USER:
        return Response({"error": "Only normal users can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        serializer = UserDetailsSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = UserDetailsSerializer(
            user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
'''


# views.py


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conductor_details(request):
    """
    API to get details of the bus conductor (personal info + bus info).
    """
    # Ensure the logged-in user is a bus conductor
    if request.user.role != request.user.Role.BUS_CONDUCTOR:
        return Response({"error": "Only bus conductors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    # Fetch the BusConductorProfile for the current user
    try:
        conductor_profile = BusConductorProfile.objects.get(user=request.user)
    except BusConductorProfile.DoesNotExist:
        return Response({"error": "Bus conductor profile not found."}, status=status.HTTP_404_NOT_FOUND)

    # Serialize and return the data
    serializer = BusConductorDetailsSerializer(conductor_profile)
    return Response(serializer.data, status=status.HTTP_200_OK)


class BusConductorProfileUpdateView(RetrieveUpdateAPIView):
    """
    API to update bus conductor profile details.
    """
    serializer_class = BusConductorDetailsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Ensure the user is a Bus Conductor and return only their profile.
        """
        user = self.request.user

        if user.role != User.Role.BUS_CONDUCTOR:
            return Response({"error": "Only bus conductors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

        # Fetch and return the related BusConductorProfile instance
        return BusConductorProfile.objects.get(user=user)

    def put(self, request, *args, **kwargs):
        """
        Handle full update (PUT)
        """
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        """
        Handle partial updates (PATCH)
        """
        return self.partial_update(request, *args, **kwargs)


@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
def bus_management(request):
    user = request.user

    if user.role != user.Role.BUS_CONDUCTOR:
        return Response({"error": "Only Bus Conductors can manage buses."}, status=status.HTTP_403_FORBIDDEN)

    bus = Buses.objects.filter(owner=user).first()

    if request.method == "GET":
        if not bus:
            return Response({"message": "No bus found for this user."}, status=status.HTTP_404_NOT_FOUND)
        serializer = BusSerializer(bus)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "POST":
        if bus:
            return Response({
                "error": "You already have a registered bus. Use PUT to update it."
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = BusSerializer(
            data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(owner=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "PUT":
        if not bus:
            return Response({"error": "No bus found to update. Please create one first."}, status=status.HTTP_404_NOT_FOUND)

        serializer = BusSerializer(
            bus,
            data=request.data,
            partial=False,  # Full update
            context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bus_approval_status(request):
    """
    Fetches the currently logged-in Bus Conductor's bus approval status.
    """
    user = request.user

    # Ensure the user is a Bus Conductor
    if user.role != user.Role.BUS_CONDUCTOR:
        return Response({"error": "Only Bus Conductors can access this API."}, status=status.HTTP_403_FORBIDDEN)

    # Retrieve the bus owned by the logged-in conductor
    bus = Buses.objects.filter(owner=user).first()

    if not bus:
        return Response({"message": "No bus found Please Add a bus in the account Page"}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        "bus_name": bus.bus_name,
        "bus_number": bus.bus_number,
        "is_approved": bus.is_approved
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def check_update(request):
    user_version = request.GET.get('current_app_version', None)

    if not user_version:
        return Response({"error": "Version parameter is required"}, status=400)

    try:
        latest_version = AppVersion.objects.latest(
            'created_at')  # Get the newest version
    except AppVersion.DoesNotExist:
        return Response({"error": "No version info available"}, status=500)

    update_required = user_version < latest_version.version  # Compare versions

    return Response({
        "update_required": update_required,
        "latest_version": latest_version.version,
        "update_url": latest_version.update_url if update_required else None
    })
