"""
URL configuration for passenger project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from busstops import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/booking_search/', views.booking_search, name='booking_search'),
    path('api/instant_booking_search/', views.instant_booking_search,
         name='instant_booking_search'),
    path('', views.home, name='home'),
    path('api/suggestions/', views.get_suggestions,
         name='get_suggestions'),
    path('api/booking_details/',
         views.fetch_booking_details, name='booking_details'),
    path('api/members/', include('members.urls')),
    path('api/booking/', include('booking.urls')),
    path('api/conductor/', include('conductor.urls')),
    path('api/live_location/', include('live_location.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)

admin.site.site_header = 'Passenger Admin'
admin.site.site_title = 'Passenger App '
