from django.contrib import admin
from .models import ConAppVersion

# Customizing the User Admin


@admin.register(ConAppVersion)
class ConAppVersionAdmin(admin.ModelAdmin):
    list_display = ("version", "update_url", "created_at")

