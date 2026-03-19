from django.db import models
from users.models import User


class Client(models.Model):
    contractor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clients')
    name = models.CharField('Nombre / Razón Social', max_length=200)
    rut = models.CharField('RUT', max_length=12, blank=True)
    phone = models.CharField('Teléfono', max_length=20, blank=True)
    email = models.EmailField('Email', blank=True)
    address = models.CharField('Dirección del Proyecto', max_length=300, blank=True)
    city = models.CharField('Ciudad', max_length=100, blank=True)
    notes = models.TextField('Notas', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cliente'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def budget_count(self):
        return self.budgets.count()
