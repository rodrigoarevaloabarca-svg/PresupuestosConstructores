from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from users.validators import validate_image_upload
import re


def validate_rut(value):
    rut = value.replace('.', '').replace('-', '').upper().strip()
    if not re.match(r'^\d{7,8}[0-9K]$', rut):
        raise ValidationError('RUT inválido. Ejemplo válido: 12345678-9')


RUBROS = [
    ('gasfiteria', 'Gasfitería'),
    ('electricidad', 'Electricidad'),
    ('construccion', 'Construcción General'),
    ('carpinteria', 'Carpintería'),
    ('pintura', 'Pintura'),
    ('ceramica', 'Cerámica y Pisos'),
    ('climatizacion', 'Climatización / HVAC'),
    ('techumbres', 'Techumbres'),
    ('otro', 'Otro'),
]

PLANS = [
    ('free', 'Plan Básico'),
    ('pro', 'Plan Pro'),
]


class User(AbstractUser):
    email = models.EmailField(unique=True)
    plan = models.CharField(max_length=10, choices=PLANS, default='free')
    plan_expires_at = models.DateTimeField(null=True, blank=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def is_pro(self):
        if hasattr(self, '_pro_cache'):
            return self._pro_cache
        from django.utils.timezone import now
        today = now().date()
        result = self.subscriptions.filter(
            status='active', next_billing_date__gte=today
        ).exists()
        # Fallback: plan field manual (legado)
        if not result and self.plan == 'pro':
            result = self.plan_expires_at is None or self.plan_expires_at > now()
        self._pro_cache = result
        return result

    def __str__(self):
        return self.email


SUBSCRIPTION_STATUS = [
    ('pending', 'Pendiente'),
    ('active', 'Activo'),
    ('cancelled', 'Cancelado'),
    ('past_due', 'Vencido'),
]


class Subscription(models.Model):
    contractor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    mp_preapproval_id = models.CharField('ID preapproval MP', max_length=100, blank=True)
    status = models.CharField('Estado', max_length=20, choices=SUBSCRIPTION_STATUS, default='pending')
    amount_clp = models.PositiveIntegerField('Monto CLP', default=0)
    next_billing_date = models.DateField('Próxima cobranza', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Suscripción'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.contractor.email} — {self.get_status_display()}"


class Payment(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    mp_payment_id = models.CharField('ID pago MP', max_length=100)
    amount = models.PositiveIntegerField('Monto CLP')
    paid_at = models.DateTimeField('Fecha de pago')

    class Meta:
        verbose_name = 'Pago'
        ordering = ['-paid_at']

    def __str__(self):
        return f"Pago {self.mp_payment_id} — ${self.amount:,}"


class ContractorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company_name = models.CharField('Nombre Empresa', max_length=200)
    rut = models.CharField('RUT', max_length=12, validators=[validate_rut])
    rubro = models.CharField('Rubro', max_length=50, choices=RUBROS, default='construccion')
    phone = models.CharField('Teléfono', max_length=20)
    address = models.CharField('Dirección', max_length=300, blank=True)
    city = models.CharField('Ciudad', max_length=100, default='Santiago')
    logo = models.ImageField('Logo', upload_to='logos/', null=True, blank=True, validators=[validate_image_upload])
    brand_color = models.CharField('Color Principal', max_length=7, default='#1e40af')
    website = models.URLField('Sitio Web', blank=True)
    budget_validity_days = models.PositiveIntegerField('Validez (días)', default=15)
    payment_terms = models.TextField('Condiciones de Pago', default='50% al inicio, 50% al finalizar la obra.')
    notes_template = models.TextField('Notas por defecto', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil de Contratista'

    def __str__(self):
        return self.company_name
