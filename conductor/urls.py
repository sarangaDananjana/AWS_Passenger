from django.urls import path
from .views import add_bus_trip, view_bus_trip_details, search_bus_routes, get_revenue_report, get_upcoming_trips, verify_booking, get_bus_trip_revenue, fetch_booking_details_for_conductor, cancel_bus_trip, get_last_7_trips_with_bookings, con_app_check_update

urlpatterns = [
    path('add-bus-trip/', add_bus_trip, name='add_bus_trip'),
    path('view-bus-trip-details/<int:trip_id>/',
         view_bus_trip_details, name='view_bus_trip_details'),
    path('search-bus-routes/', search_bus_routes, name='search_bus_routes'),
    path('home/', get_revenue_report, name='home'),
    path('get_trip_details', fetch_booking_details_for_conductor,
         name='fetch_booking_details_for_conductor'),
    path('upcoming-trips/', get_upcoming_trips, name='upcoming_trips'),
    path('qr_scan/', verify_booking, name='qr_scan'),
    path('revenue/', get_bus_trip_revenue, name='revenue'),
    path('cancel-bus-trip/<int:trip_id>/',
         cancel_bus_trip, name='cancel-bus-trip'),
    path('last-7-bookings-home/', get_last_7_trips_with_bookings,
         name='get_last_7_bookings_for_home'),
    path('con_app_android-app-version/',
         con_app_check_update, name='con_app_update_check'),


]
