from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from .models import Client
from .serializers import ClientSerializer
from users.plan_guard import PlanGuard


class ClientListAPIView(generics.ListCreateAPIView):
    serializer_class = ClientSerializer

    def get_queryset(self):
        return Client.objects.filter(contractor=self.request.user)

    def perform_create(self, serializer):
        allowed, msg = PlanGuard.can_create_client(self.request.user)
        if not allowed:
            raise PermissionDenied(msg)
        serializer.save(contractor=self.request.user)


class ClientDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ClientSerializer

    def get_queryset(self):
        return Client.objects.filter(contractor=self.request.user)
