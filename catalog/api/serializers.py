from rest_framework import serializers

from catalog.models import Product, RetailerProduct


class CatalogProductSuggestionSerializer(serializers.ModelSerializer):
    source = serializers.SerializerMethodField()
    price = serializers.IntegerField(source="sale_price")

    class Meta:
        model = Product
        fields = ["source", "name", "price", "unit"]

    def get_source(self, obj):
        return "catalog"


class RetailerProductSuggestionSerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="retailer")
    price = serializers.IntegerField(source="price_clp")

    class Meta:
        model = RetailerProduct
        fields = ["source", "name", "price", "url"]
