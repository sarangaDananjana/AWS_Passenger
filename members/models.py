import random
import datetime
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.db import models
from django.core.mail import send_mail
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver

MALE = 'M'
FEMALE = 'F'
OTHER = 'O'

GENDER_CHOICES = [
    (MALE, 'Male'),
    (FEMALE, 'Female'),
    (OTHER, 'Other')
]


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        NORMAL_USER = "NORMAL_USER", "Normal User"
        BUS_CONDUCTOR = "BUS_CONDUCTOR", "Bus Conductor"

    username = None
    phone_number = models.CharField(
        max_length=15,  blank=True, null=True, unique=True)
    gender = models.CharField(
        max_length=1, choices=GENDER_CHOICES, default=MALE,  blank=True, null=True)
    birthday = models.DateField(null=True, blank=True)

    role = models.CharField(
        max_length=50, choices=Role.choices, default=Role.NORMAL_USER)
    is_verified = models.BooleanField(
        default=False)  # 🆕 Tracks OTP verification
    otp_code = models.CharField(
        max_length=6, blank=True, null=True)  # 🆕 Stores OTP
    otp_expires_at = models.DateTimeField(blank=True, null=True)

    email_otp_code = models.CharField(max_length=6, blank=True, null=True)
    email_otp_expires_at = models.DateTimeField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.phone_number}"

    def generate_otp(self):
        """Generate a 6-digit OTP and set expiration time."""
        self.otp_code = str(random.randint(100000, 999999))  # 6-digit OTP
        # OTP valid for 10 minutes
        self.otp_expires_at = now() + datetime.timedelta(minutes=10)
        self.save()

    def generate_email_otp(self):
        """
        Generate a 6-digit OTP for email verification.
        """
        self.email_otp_code = str(random.randint(
            100000, 999999))  # Generate 6-digit OTP
        # OTP expiry set to 10 minutes
        self.email_otp_expires_at = now() + datetime.timedelta(minutes=10)
        self.save()
        self.send_email_otp()  # Send the OTP to the user's email

    def send_email_otp(self):
        """
        Sends OTP to the user's email address.
        """
        send_mail(
            subject="Your Email Verification Code",
            message=f"Your OTP code for email verification is: {self.email_otp_code}",
            # Replace with your actual email address
            from_email="fission.web.studio@gmail.com",
            recipient_list=[self.email],
            fail_silently=False,
        )


class NormalUserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.FileField(
        upload_to='images/profile_pics', null=True, blank=True)
    customer_id = models.CharField(max_length=255, null=True, blank=True)
    lane_1 = models.CharField(max_length=255, null=True, blank=True)
    lane_2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    postal_code = models.CharField(max_length=255, null=True, blank=True)


class BusConductorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nic_number = models.CharField(max_length=255, null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    machine = models.BooleanField(default=False)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == User.Role.NORMAL_USER:
            NormalUserProfile.objects.create(user=instance)
        elif instance.role == User.Role.BUS_CONDUCTOR:
            BusConductorProfile.objects.create(user=instance)


User = get_user_model()


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('TRIP_STARTED', 'Trip Started'),
        ('BOOKING_CONFIRMATION', 'Booking Confirmation'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.phone_number} - {self.notification_type}"


class AppVersion(models.Model):
    version = models.CharField(max_length=10, unique=True)
    update_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.version}"
