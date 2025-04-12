from django.urls import path
from .views import book_seat, user_booking_history, home_ongoing_bookings, get_notifications, mark_notifications_as_read, get_ticket_details, reschedule_booking, cancel_booking

urlpatterns = [
    path('book-seat/', book_seat, name='book_seat'),
    path('reschedule/', reschedule_booking, name='reschedule'),
    path('cancel-booking/<int:booking_id>/',
         cancel_booking, name='cancel_booking'),
    path('booking-history/', user_booking_history, name='user_booking_history'),
    path('ongoing-bookings/', home_ongoing_bookings,
         name='home_ongoing_bookings'),
    path('notifications/', get_notifications, name='get_notifications'),
    path('notifications/read/', mark_notifications_as_read,
         name='mark_notifications_as_read'),
    path('ticket/<int:booking_id>/', get_ticket_details, name='get_ticket_details'),
]
