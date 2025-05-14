from django.urls import path
from .views import login_conductor, route_sections

urlpatterns = [
    path('api/machine/login/', login_conductor, name='machine_login'),
    path('api/machine/<int:route_id>/', route_sections, name='route_sections'),
]
