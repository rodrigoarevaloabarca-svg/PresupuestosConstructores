from rest_framework import generics
from .models import Client
from .serializers import ClientSerializer


class ClientListAPIView(generics.ListCreateAPIView):
    serializer_class = ClientSerializer

    def get_queryset(self):
        return Client.objects.filter(contractor=self.request.user)

    def perform_create(self, serializer):
        serializer.save(contractor=self.request.user)


class ClientDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ClientSerializer

    def get_queryset(self):
        return Client.objects.filter(contractor=self.request.user)
