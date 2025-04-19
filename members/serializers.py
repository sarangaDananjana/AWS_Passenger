from .models import User, BusConductorProfile, AppVersion
from busstops.models import Buses
from rest_framework import serializers
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=User.Role.choices)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number',
                  'gender', 'password', 'role', 'birthday']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            phone_number=validated_data.get('phone_number', ''),
            gender=validated_data.get('gender', ''),
            password=validated_data['password'],
            role=validated_data['role'],
            birthday=validated_data.get('birthday')  # Store birthday
        )
        return user


class BusConductorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusConductorProfile
        fields = ['nic_number', 'full_name', 'address']


class UserDetailsSerializer(serializers.ModelSerializer):
    profile_pic = serializers.ImageField(
        source='ormaluserprofile.profile_pic', required=False)
    bus_conductor_profile = BusConductorProfileSerializer(required=False)

    customer_id = serializers.CharField(
        source='normaluserprofile.customer_id', required=False)
    lane_1 = serializers.CharField(
        source='normaluserprofile.lane_1', required=False)
    lane_2 = serializers.CharField(
        source='normaluserprofile.lane_2', required=False)
    city = serializers.CharField(
        source='normaluserprofile.city', required=False)
    postal_code = serializers.CharField(
        source='normaluserprofile.postal_code', required=False)

    class Meta:
        model = User
        fields = ['email', "is_email_verified", 'phone_number', 'gender',
                  'profile_pic', 'first_name', 'last_name', 'birthday', 'bus_conductor_profile', 'lane_1', 'lane_2', 'city', 'postal_code']
        read_only_fields = ['phone_number']  # Phone number cannot be edited

    def update(self, instance, validated_data):
        """
        Allow users to update their birthday, gender, email, first name, last name, and profile picture.
        """

        bus_conductor_data = validated_data.pop('bus_conductor_profile', None)
        profile_data = validated_data.pop('normal_user_profile', {})

        instance.email = validated_data.get('email', instance.email)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.first_name = validated_data.get(
            'first_name', instance.first_name)
        instance.last_name = validated_data.get(
            'last_name', instance.last_name)
        instance.birthday = validated_data.get('birthday', instance.birthday)
        instance.save()

        normal_user_profile = instance.normal_user_profile
        for field, value in profile_data.items():
            setattr(normal_user_profile, field, value)
        normal_user_profile.save()

        if instance.role == User.Role.BUS_CONDUCTOR and bus_conductor_data:
            profile, created = BusConductorProfile.objects.get_or_create(
                user=instance)
            for attr, value in bus_conductor_data.items():
                setattr(profile, attr, value)
            profile.save()

        '''
        # Handle profile picture update
        profile_data = validated_data.get('normal_user_profile', {})
        profile = instance.normal_user_profile
        if 'profile_pic' in profile_data:
            profile.profile_pic = profile_data['profile_pic']
            profile.save()
        '''
        return instance


class BusConductorDetailsSerializer(serializers.ModelSerializer):
    # Conductor's Personal Information
    phone_number = serializers.CharField(source='user.phone_number')
    is_verified = serializers.BooleanField(source='user.is_verified')
    nic_number = serializers.CharField()
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    address = serializers.CharField()

    # Bus Information
    bus_number = serializers.CharField(source='user.bus.bus_number')
    bus_name = serializers.CharField(source='user.bus.bus_name')
    seat_count = serializers.IntegerField(source='user.bus.seat_count')
    bus_type = serializers.CharField(source='user.bus.bus_type')
    route_permit_number = serializers.CharField(
        source='user.bus.route_permit_number')
    is_approved = serializers.BooleanField(source='user.bus.is_approved')

    class Meta:
        model = BusConductorProfile  # Assuming the relationship is through this model
        fields = [
            'phone_number', 'is_verified', 'nic_number', 'first_name', 'last_name', 'address', 'full_name',
            'bus_number', 'bus_name', 'seat_count', 'bus_type', 'route_permit_number', 'is_approved'
        ]


class BusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buses
        fields = ['bus_name', 'bus_number', 'seat_count',
                  'bus_type', 'route_permit_number', 'route_permit_image', 'is_approved']

    def create(self, validated_data):
        """
        Override create method to assign the logged-in user as the bus owner.
        """
        request = self.context['request']
        user = request.user

        # Ensure only Bus Conductors can create a bus
        if user.role != User.Role.BUS_CONDUCTOR:
            raise serializers.ValidationError(
                "Only Bus Conductors can add a bus.")

        # Assign the logged-in conductor as the bus owner
        validated_data['owner'] = user
        return super().create(validated_data)


class AppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = ['version', 'update_url']
