from django.apps import AppConfig


class CoreDataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.coredata"          # ← 这里一定要写 apps.coredata
    verbose_name = "Core Performance Data"