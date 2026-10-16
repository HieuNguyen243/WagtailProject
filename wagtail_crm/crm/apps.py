# crm/apps.py

from django.apps import AppConfig


class CrmConfig(AppConfig):
    name = "crm"
    verbose_name = "Hệ thống Quản lý CRM"

    def ready(self):
        import crm.signals  # noqa
