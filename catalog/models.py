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

    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"

    @property
    def margin(self):
        if self.cost_price > 0:
            return round(((self.sale_price - self.cost_price) / self.cost_price) * 100, 1)
        return 0
