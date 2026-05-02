import re

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from users.validators import validate_image_upload


def validate_rut(value):
    rut = value.replace(".", "").replace("-", "").upper().strip()
    if not re.match(r"^\d{7,8}[0-9K]$", rut):
        raise ValidationError("RUT inválido. Ejemplo válido: 12345678-9")


RUBROS = [
    ("gasfiteria", "Gasfitería"),
    ("electricidad", "Electricidad"),
    ("construccion", "Construcción General"),
    ("carpinteria", "Carpintería"),
    ("pintura", "Pintura"),
    ("ceramica", "Cerámica y Pisos"),
    ("climatizacion", "Climatización / HVAC"),
    ("techumbres", "Techumbres"),
    ("otro", "Otro"),
]

PLANS = [
    ("free", "Plan Básico"),
    ("pro", "Plan Pro"),
]


class User(AbstractUser):
    email = models.EmailField(unique=True)
    plan = models.CharField(max_length=10, choices=PLANS, default="free")
    plan_expires_at = models.DateTimeField(null=True, blank=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def is_pro(self):
        # Sistema gratuito — siempre Pro. Lógica legacy en git history.
        return True

    def __str__(self):
        return self.email


SUBSCRIPTION_STATUS = [
    ("pending", "Pendiente"),
    ("active", "Activo"),
    ("cancelled", "Cancelado"),
    ("past_due", "Vencido"),
]


class Subscription(models.Model):
    contractor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    mp_preapproval_id = models.CharField("ID preapproval MP", max_length=100, blank=True)
    status = models.CharField("Estado", max_length=20, choices=SUBSCRIPTION_STATUS, default="pending")
    amount_clp = models.PositiveIntegerField("Monto CLP", default=0)
    next_billing_date = models.DateField("Próxima cobranza", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Suscripción"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.contractor.email} — {self.get_status_display()}"


class Payment(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="payments")
    mp_payment_id = models.CharField("ID pago MP", max_length=100)
    amount = models.PositiveIntegerField("Monto CLP")
    paid_at = models.DateTimeField("Fecha de pago")

    class Meta:
        verbose_name = "Pago"
        ordering = ["-paid_at"]

    def __str__(self):
        return f"Pago {self.mp_payment_id} — ${self.amount:,}"


class ContractorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    company_name = models.CharField("Nombre Empresa", max_length=200)
    rut = models.CharField("RUT", max_length=12, validators=[validate_rut])
    rubro = models.CharField("Rubro", max_length=50, choices=RUBROS, default="construccion")
    phone = models.CharField("Teléfono", max_length=20)
    address = models.CharField("Dirección", max_length=300, blank=True)
    city = models.CharField("Ciudad", max_length=100, default="Santiago")
    logo = models.ImageField("Logo", upload_to="logos/", null=True, blank=True, validators=[validate_image_upload])
    brand_color = models.CharField("Color Principal", max_length=7, default="#1e40af")
    website = models.URLField("Sitio Web", blank=True)
    budget_validity_days = models.PositiveIntegerField("Validez (días)", default=15)
    payment_terms = models.TextField("Condiciones de Pago", default="50% al inicio, 50% al finalizar la obra.")
    notes_template = models.TextField("Notas por defecto", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil de Contratista"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_logo = self.logo.name if self.logo else None

    def save(self, *args, **kwargs):
        if self.logo and self.logo.name != self._original_logo:
            self._sanitize_logo()
        super().save(*args, **kwargs)

    def _sanitize_logo(self):
        """Re-encodea la imagen para eliminar EXIF y payloads. Redimensiona a máx 800px."""
        from io import BytesIO

        from django.core.files.base import ContentFile
        from PIL import Image

        max_dim = 800
        try:
            import contextlib

            img = Image.open(self.logo)
            has_alpha = img.mode in ("RGBA", "LA", "P")
            img = img.convert("RGBA" if has_alpha else "RGB")
            if max(img.size) > max_dim:
                img.thumbnail((max_dim, max_dim), Image.LANCZOS)
            buf = BytesIO()
            fmt, ext = ("PNG", "png") if has_alpha else ("JPEG", "jpg")
            img.save(buf, format=fmt, optimize=True)
            buf.seek(0)
            if self._original_logo:
                from django.core.files.storage import default_storage

                with contextlib.suppress(Exception):
                    default_storage.delete(self._original_logo)
            self.logo.save(f"logo_{self.user_id}.{ext}", ContentFile(buf.read()), save=False)
        except Exception:
            pass

    def __str__(self):
        return self.company_name
