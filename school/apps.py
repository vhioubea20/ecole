from django.apps import AppConfig


class SchoolConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "school"
    verbose_name = "Gestion scolaire"

    def ready(self):
        from . import signals