from rest_framework import generics
from .models import Product
from .serializers import ProductSerializer


class ProductListAPIView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        qs = Product.objects.filter(contractor=self.request.user, is_active=True)
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

    def perform_create(self, serializer):
        serializer.save(contractor=self.request.user)


class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(contractor=self.request.user)
