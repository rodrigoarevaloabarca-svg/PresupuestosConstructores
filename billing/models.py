from django.db import models, transaction

from users.models import User

TIPO_DTE_CHOICES = [
    (33, "Factura Electrónica"),
    (39, "Boleta Electrónica"),
]

INVOICE_STATUS_CHOICES = [
    ("pending", "Pendiente"),
    ("accepted", "Aceptada"),
    ("rejected", "Rechazada"),
]


class Invoice(models.Model):
    contractor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invoices")
    budget = models.OneToOneField(
        "budgets.Budget",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoice",
    )
    folio = models.PositiveIntegerField("Folio")
    tipo_dte = models.PositiveSmallIntegerField("Tipo DTE", choices=TIPO_DTE_CHOICES, default=39)
    sii_track_id = models.CharField("Track ID SII", max_length=100, blank=True)
    xml_url = models.URLField("URL XML", blank=True)
    pdf_url = models.URLField("URL PDF", blank=True)
    status = models.CharField("Estado", max_length=20, choices=INVOICE_STATUS_CHOICES, default="pending")
    issued_at = models.DateTimeField("Emitida el", auto_now_add=True)
    total_clp = models.PositiveIntegerField("Total CLP")

    class Meta:
        verbose_name = "Factura/Boleta"
        unique_together = [["contractor", "tipo_dte", "folio"]]
        indexes = [
            models.Index(fields=["contractor", "status"]),
        ]

    def __str__(self):
        return f"DTE {self.tipo_dte} Folio {self.folio} — {self.contractor.email}"

    def save(self, *args, **kwargs):
        if not self.folio:
            with transaction.atomic():
                last = Invoice.objects.select_for_update().filter(contractor=self.contractor, tipo_dte=self.tipo_dte).order_by("-folio").first()
                self.folio = (last.folio + 1) if last else 1
        super().save(*args, **kwargs)


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    name = models.CharField("Descripción", max_length=300)
    quantity = models.DecimalField("Cantidad", max_digits=10, decimal_places=2)
    unit_price = models.PositiveIntegerField("Precio Unitario CLP")
    subtotal = models.PositiveIntegerField("Subtotal CLP")

    class Meta:
        verbose_name = "Línea de Factura"

    def __str__(self):
        return self.name
