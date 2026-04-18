from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'billing'
    verbose_name = 'Facturación'

    def ready(self):
        import users.signals  # noqa: F401
