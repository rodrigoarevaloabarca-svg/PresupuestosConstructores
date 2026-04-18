from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = 'catalog'

    def ready(self):
        from auditlog.registry import auditlog
        from catalog.models import Product
        auditlog.register(Product)
