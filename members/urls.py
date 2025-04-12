from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import register_or_login_user, logout_user, user_details, verify_otp, verify_email_otp, get_conductor_details, BusConductorProfileUpdateView, bus_management, bus_approval_status, check_update ,register_or_login_conductor


urlpatterns = [
    path('login/', register_or_login_user, name='login_user'),  # Login & get tokens
    path('login-conductor/', register_or_login_conductor, name='login_conductor'),
    path('logout/', logout_user, name='logout_user'),  # Blacklist refresh token
    path('me/', user_details, name='user_details'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-email-otp/', verify_email_otp, name='verify_email_otp'),
    path('conductor-details/', get_conductor_details, name='conductor_details'),
    path('user-details-update/',
         BusConductorProfileUpdateView.as_view(), name='update_user'),
    path('bus-details-update/', bus_management, name='update_bus'),
    path('approval-status/', bus_approval_status, name='bus-approval-status'),
    path('android-app-version/', check_update, name='update_check'),

]
