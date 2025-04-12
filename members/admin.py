from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, NormalUserProfile, BusConductorProfile, AppVersion

# Customizing the User Admin


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = ("version", "update_url", "created_at")


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("phone_number","password")}),
        ("Personal info", {"fields": ("first_name",
         "last_name", "email", "gender", "birthday")}),
        ("Permissions", {"fields": ("is_active", "is_staff",
         "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Role Info", {"fields": ("role",)}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("password1", "password2", "email", "birthday", "first_name", "last_name", "phone_number", "gender", "role"),
        }),
    )
    list_display = ("id", "phone_number", "email", "first_name",
                    "last_name", "role", "is_staff", "is_verified", "is_active")
    list_filter = ("role", "is_staff", "is_active", "gender")
    search_fields = ("email", "first_name",
                     "last_name", "phone_number")
    ordering = ("phone_number",)

# Inline Admin for NormalUserProfile


class NormalUserProfileInline(admin.StackedInline):
    model = NormalUserProfile
    can_delete = False
    verbose_name_plural = "Normal User Profiles"

# Inline Admin for BusConductorProfile


class BusConductorProfileInline(admin.StackedInline):
    model = BusConductorProfile
    can_delete = False
    verbose_name_plural = "Bus Conductor Profiles"

# Admin for NormalUserProfile


@admin.register(NormalUserProfile)
class NormalUserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "profile_pic")
    search_fields = ("user__email",)
    list_filter = ("user__gender",)

# Admin for BusConductorProfile


@admin.register(BusConductorProfile)
class BusConductorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "nic_number", "full_name", "address")
    search_fields = ("nic_number", "full_name")
    list_filter = ("user__gender",)

# Connecting Inline Profiles with User Admin


class UserAdminWithProfiles(CustomUserAdmin):
    inlines = []

    def get_inlines(self, request, obj=None):
        if obj:
            if obj.role == User.Role.NORMAL_USER:
                return [NormalUserProfileInline]
            elif obj.role == User.Role.BUS_CONDUCTOR:
                return [BusConductorProfileInline]
        return []


# Registering the Custom User Admin with Inline Profiles
admin.site.unregister(User)
admin.site.register(User, UserAdminWithProfiles)
