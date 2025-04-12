from django.apps import AppConfig


class BusstopsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'busstops'

    def ready(self):
        import busstops.signals
