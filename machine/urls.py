from django.urls import path
from .views import login_conductor, route_sections

urlpatterns = [
    path('login/', login_conductor, name='machine_login'),
    path('<int:route_id>/', route_sections, name='route_sections'),
]
