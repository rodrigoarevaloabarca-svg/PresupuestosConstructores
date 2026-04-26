from django.apps import AppConfig


class ClientsConfig(AppConfig):
    name = 'clients'

    def ready(self):
        from auditlog.registry import auditlog

        from clients.models import Client
        auditlog.register(Client)
