import contextlib
from datetime import timedelta

from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone

from budgets.managers import BudgetQuerySet
from catalog.models import UNIT_CHOICES, Product
from clients.models import Client
from users.models import User

RECIPE_RUBROS = [
    "Pintura",
    "Cerámica",
    "Pisos",
    "Construcción",
    "Terminaciones",
    "Gasfitería",
    "Electricidad",
    "Otro",
]

STATUS_CHOICES = [
    ("borrador", "Borrador"),
    ("enviado", "Enviado al Cliente"),
    ("aceptado", "Aceptado"),
    ("rechazado", "Rechazado"),
    ("vencido", "Vencido"),
]


class Budget(models.Model):
    objects = BudgetQuerySet.as_manager()

    contractor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="budgets")
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="budgets")
    number = models.PositiveIntegerField("N° Presupuesto", null=True, blank=True)
    version = models.PositiveIntegerField("Versión", default=1)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="versions")
    is_template = models.BooleanField("Es plantilla", default=False)
    title = models.CharField("Título / Obra", max_length=300)
    status = models.CharField("Estado", max_length=20, choices=STATUS_CHOICES, default="borrador")
    validity_days = models.PositiveIntegerField("Validez (días)", default=15)
    payment_terms = models.TextField("Condiciones de Pago", blank=True)
    notes = models.TextField("Notas", blank=True)
    tax_percent = models.DecimalField("IVA %", max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Presupuesto"
        ordering = ["-created_at"]
        unique_together = [["contractor", "number", "version"]]
        indexes = [
            models.Index(fields=["contractor", "status"]),
            models.Index(fields=["contractor", "-created_at"]),
            models.Index(fields=["contractor", "sent_at"]),
            models.Index(fields=["contractor", "is_template"]),
        ]

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
        if hasattr(self, "_subtotal_materials"):
            return self._subtotal_materials or 0
        return sum(item.total for item in self.material_items.all())

    @property
    def subtotal_labor(self):
        if hasattr(self, "_subtotal_labor"):
            return self._subtotal_labor or 0
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
        if not self.is_template and not self.number:
            with transaction.atomic():
                last = Budget.objects.select_for_update().filter(contractor=self.contractor, is_template=False).exclude(number=None).order_by("-number").first()
                self.number = (last.number + 1) if last else 1
        if not self.payment_terms:
            with contextlib.suppress(AttributeError):
                self.payment_terms = self.contractor.profile.payment_terms
        super().save(*args, **kwargs)


class BudgetItemMaterial(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="material_items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField("Descripción", max_length=300)
    unit = models.CharField("Unidad", max_length=10, choices=UNIT_CHOICES, default="un")
    quantity = models.DecimalField("Cantidad", max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField("Precio Unitario", max_digits=12, decimal_places=0, validators=[MinValueValidator(0)])
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    @property
    def total(self):
        return round(self.quantity * self.unit_price)

    def __str__(self):
        return self.name


class BudgetItemLabor(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="labor_items")
    name = models.CharField("Descripción del Trabajo", max_length=300)
    unit = models.CharField("Unidad", max_length=10, choices=UNIT_CHOICES, default="gl")
    quantity = models.DecimalField("Cantidad / Horas", max_digits=10, decimal_places=2, default=1, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField("Precio Unitario", max_digits=12, decimal_places=0, validators=[MinValueValidator(0)])
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    @property
    def total(self):
        return round(self.quantity * self.unit_price)

    def __str__(self):
        return self.name


class BudgetSignature(models.Model):
    """Firma digital del cliente sobre la vista pública del presupuesto."""

    budget = models.OneToOneField(Budget, on_delete=models.CASCADE, related_name="signature")
    signature_png = models.ImageField("Firma PNG", upload_to="budgets/signatures/%Y/%m/")
    hash_sha256 = models.CharField("SHA-256", max_length=64)
    ip = models.GenericIPAddressField("IP del firmante")
    user_agent = models.TextField("User-Agent", blank=True)
    signed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Firma de presupuesto #{self.budget.number}"


class BudgetAttachment(models.Model):
    """Archivos adjuntos (fotos, planos, PDFs) de un presupuesto."""

    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField("Archivo", upload_to="budgets/attachments/%Y/%m/")
    filename = models.CharField("Nombre del archivo", max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return self.filename


class MaterialRecipe(models.Model):
    contractor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recipes")
    name = models.CharField("Nombre", max_length=200)
    rubro = models.CharField("Categoría", max_length=50)
    icon = models.CharField("Ícono", max_length=10, default="📦")
    input_label = models.CharField("Etiqueta de medida", max_length=100, default="Superficie")
    input_unit = models.CharField("Unidad de medida", max_length=20, default="m²")
    input_placeholder = models.CharField("Placeholder", max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["rubro", "name"]
        verbose_name = "Receta de materiales"
        verbose_name_plural = "Recetas de materiales"

    def __str__(self):
        return self.name

    def to_api_dict(self):
        return {
            "id": self.pk,
            "name": self.name,
            "rubro": self.rubro,
            "icon": self.icon,
            "input_label": self.input_label,
            "input_unit": self.input_unit,
            "input_placeholder": self.input_placeholder,
            "items": [{"name": i.name, "unit": i.unit, "factor": str(i.quantity_factor)} for i in self.items.all()],
        }


class MaterialRecipeItem(models.Model):
    recipe = models.ForeignKey(MaterialRecipe, on_delete=models.CASCADE, related_name="items")
    name = models.CharField("Material", max_length=200)
    unit = models.CharField("Unidad", max_length=10, choices=UNIT_CHOICES, default="un")
    quantity_factor = models.DecimalField("Factor por unidad", max_digits=8, decimal_places=4)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


def _default_token_expiry():
    return timezone.now() + timedelta(days=30)


class BudgetPublicToken(models.Model):
    """Token único para compartir un presupuesto públicamente con el cliente."""

    budget = models.OneToOneField(Budget, on_delete=models.CASCADE, related_name="public_token")
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    views = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField("Expira el", default=_default_token_expiry)
    is_revoked = models.BooleanField("Revocado", default=False)

    @property
    def is_valid(self):
        return not self.is_revoked and timezone.now() <= self.expires_at

    def save(self, *args, **kwargs):
        if not self.token:
            import secrets

            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def get_public_url(self):
        from django.urls import reverse

        return reverse("budget_public", args=[self.token])

    def __str__(self):
        return f"Token para presupuesto #{self.budget.number}"
