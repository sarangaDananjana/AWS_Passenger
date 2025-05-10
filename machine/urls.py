from django.urls import path
from .views import login_conductor

urlpatterns = [
    path('api/machine/login/', login_conductor, name='machine_login'),
]
