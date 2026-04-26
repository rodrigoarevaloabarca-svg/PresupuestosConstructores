from django.db.models import Q
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.api.serializers import (
    CatalogProductSuggestionSerializer,
    RetailerProductSuggestionSerializer,
)
from catalog.models import Product, RetailerProduct

MAX_RESULTS = 5


@method_decorator(ratelimit(key="user", rate="60/m", block=True), name="get")
class ProductSuggestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.query_params.get("q", "").strip()
        limit = min(int(request.query_params.get("limit", 10)), 20)

        if len(q) <= 2:
            return Response([])

        own = Product.objects.filter(contractor=request.user, is_active=True).filter(Q(name__icontains=q))[:MAX_RESULTS]
        own_data = CatalogProductSuggestionSerializer(own, many=True).data

        retailer_qs = RetailerProduct.objects.filter(is_active=True, name__icontains=q).order_by("-last_scraped")[: (limit - len(own_data))]
        retailer_data = RetailerProductSuggestionSerializer(retailer_qs, many=True).data

        return Response(list(own_data) + list(retailer_data))
