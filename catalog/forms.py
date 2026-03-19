from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'unit', 'cost_price', 'sale_price', 'sku']
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}