from django.apps import AppConfig


class DentalLmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dental_lms'

    def ready(self):
        import dental_lms.signals  # noqa: F401
