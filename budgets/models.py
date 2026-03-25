from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone
from datetime import timedelta
from users.models import User
from clients.models import Client
from catalog.models import Product, UNIT_CHOICES


STATUS_CHOICES = [
    ('borrador', 'Borrador'),
    ('enviado', 'Enviado al Cliente'),
    ('aceptado', 'Aceptado'),
    ('rechazado', 'Rechazado'),
    ('vencido', 'Vencido'),
]


class Budget(models.Model):
    contractor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='budgets')
    number = models.PositiveIntegerField('N° Presupuesto')
    title = models.CharField('Título / Obra', max_length=300)
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='borrador')
    validity_days = models.PositiveIntegerField('Validez (días)', default=15)
    payment_terms = models.TextField('Condiciones de Pago', blank=True)
    notes = models.TextField('Notas', blank=True)
    tax_percent = models.DecimalField('IVA %', max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Presupuesto'
        ordering = ['-created_at']
        unique_together = [['contractor', 'number']]

    def __str__(self):
        return f"#{self.number} - {self.title}"

    @property
    def valid_until(self):
        return self.created_at + timedelta(days=self.validity_days)

    @property
    def is_expired(self):
        return timezone.now() > self.valid_until

    @property
    def subtotal_materials(self):
        return sum(item.total for item in self.material_items.all())

    @property
    def subtotal_labor(self):
        return sum(item.total for item in self.labor_items.all())

    @property
    def subtotal(self):
        return self.subtotal_materials + self.subtotal_labor

    @property
    def tax_amount(self):
        return round(self.subtotal * self.tax_percent / 100)

    @property
    def total(self):
        return self.subtotal + self.tax_amount

    def save(self, *args, **kwargs):
        if not self.number:
            with transaction.atomic():
                last = (
                    Budget.objects.select_for_update()
                    .filter(contractor=self.contractor)
                    .order_by('-number')
                    .first()
                )
                self.number = (last.number + 1) if last else 1
        if not self.payment_terms:
            try:
                self.payment_terms = self.contractor.profile.payment_terms
            except Exception:
                pass
        super().save(*args, **kwargs)


class BudgetItemMaterial(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='material_items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField('Descripción', max_length=300)
    unit = models.CharField('Unidad', max_length=10, choices=UNIT_CHOICES, default='un')
    quantity = models.DecimalField('Cantidad', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField('Precio Unitario', max_digits=12, decimal_places=0, validators=[MinValueValidator(0)])
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    @property
    def total(self):
        return round(self.quantity * self.unit_price)

    def __str__(self):
        return self.name


class BudgetItemLabor(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='labor_items')
    name = models.CharField('Descripción del Trabajo', max_length=300)
    unit = models.CharField('Unidad', max_length=10, choices=UNIT_CHOICES, default='gl')
    quantity = models.DecimalField('Cantidad / Horas', max_digits=10, decimal_places=2, default=1, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField('Precio Unitario', max_digits=12, decimal_places=0, validators=[MinValueValidator(0)])
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    @property
    def total(self):
        return round(self.quantity * self.unit_price)

    def __str__(self):
        return self.name


class BudgetPublicToken(models.Model):
    """Token único para compartir un presupuesto públicamente con el cliente."""
    budget = models.OneToOneField(Budget, on_delete=models.CASCADE, related_name='public_token')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    views = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.token:
            import secrets
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def get_public_url(self):
        from django.urls import reverse
        return reverse('budget_public', args=[self.token])

    def __str__(self):
        return f"Token para presupuesto #{self.budget.number}"
