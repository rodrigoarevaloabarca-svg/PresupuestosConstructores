from django.db import models
from users.models import User

UNIT_CHOICES = [
    ('un', 'Unidad'),
    ('m2', 'm²'),
    ('m3', 'm³'),
    ('ml', 'Metro lineal'),
    ('kg', 'Kilogramo'),
    ('lt', 'Litro'),
    ('hr', 'Hora'),
    ('gl', 'Global'),
    ('bls', 'Bolsa'),
    ('pk', 'Pack'),
]

CATEGORIES = [
    ('materiales', 'Materiales'),
    ('herramientas', 'Herramientas'),
    ('electricidad', 'Eléctrico'),
    ('gasfiteria', 'Gasfitería'),
    ('ceramica', 'Cerámica'),
    ('pintura', 'Pintura'),
    ('madera', 'Madera'),
    ('otro', 'Otro'),
]


class Product(models.Model):
    contractor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    name = models.CharField('Nombre', max_length=200)
    description = models.TextField('Descripción', blank=True)
    category = models.CharField('Categoría', max_length=50, choices=CATEGORIES, default='materiales')
    unit = models.CharField('Unidad', max_length=10, choices=UNIT_CHOICES, default='un')
    cost_price = models.DecimalField('Precio Costo', max_digits=12, decimal_places=0, default=0)
    sale_price = models.DecimalField('Precio Venta', max_digits=12, decimal_places=0, default=0)
    sku = models.CharField('SKU/Código', max_length=50, blank=True)
    is_active = models.BooleanField('Activo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        ordering = ['name']
        indexes = [
            models.Index(fields=['contractor', 'is_active']),
            models.Index(fields=['contractor', 'category']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"

    @property
    def margin(self):
        if self.cost_price > 0:
            return round(((self.sale_price - self.cost_price) / self.cost_price) * 100, 1)
        return 0


RETAILER_CHOICES = [
    ('sodimac', 'Sodimac'),
    ('easy', 'Easy'),
    ('imperial', 'Ferretería Imperial'),
]


class RetailerProduct(models.Model):
    """Caché de precios de ferreterías externas (Sodimac, Easy, Imperial)."""
    retailer = models.CharField('Ferretería', max_length=20, choices=RETAILER_CHOICES)
    name = models.CharField('Nombre', max_length=500)
    sku = models.CharField('SKU', max_length=100, blank=True, null=True)
    price_clp = models.DecimalField('Precio CLP', max_digits=12, decimal_places=0)
    url = models.URLField('URL', max_length=1000)
    category = models.CharField('Categoría', max_length=200, blank=True, null=True)
    last_scraped = models.DateTimeField('Última actualización', auto_now=True)
    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Producto de Ferretería'
        verbose_name_plural = 'Productos de Ferreterías'
        unique_together = [['retailer', 'sku']]
        indexes = [
            models.Index(fields=['retailer', 'is_active']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"[{self.get_retailer_display()}] {self.name}"
