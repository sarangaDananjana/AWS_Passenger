from django.apps import AppConfig


class LiveLocationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'live_location'

    def ready(self):
        import live_location.signals  # ✅ Import the signals file
