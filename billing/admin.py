from django.contrib import admin

from .models import Invoice, InvoiceLine


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['folio', 'tipo_dte', 'contractor', 'total_clp', 'status', 'issued_at']
    list_filter = ['tipo_dte', 'status']
    search_fields = ['contractor__email', 'sii_track_id']
    inlines = [InvoiceLineInline]
