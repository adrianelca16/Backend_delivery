from django.db import models
from core.models import Usuario
from ordenes.models import Orden
from django.utils import timezone
import uuid

class MetodoPago(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()
    icons = models.CharField(max_length=255, blank=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.nombre

class Pago(models.Model):
    orden = models.ForeignKey("ordenes.Orden", on_delete=models.CASCADE, related_name="pagos")
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    metodo = models.ForeignKey(MetodoPago, on_delete=models.PROTECT)

    # Monto en divisa principal ($)
    monto_usd = models.DecimalField(max_digits=10, decimal_places=2)

    # Opcional: monto en bolívares
    monto_bs = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tasa_cambio = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)

    confirmado = models.BooleanField(default=False)
    creado_en = models.DateTimeField(default=timezone.now)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referencia = models.CharField(max_length=50, blank=True)
    telefono_pago = models.CharField(max_length=15, blank=True,null=True)

    class Meta:
        unique_together = ('orden', 'metodo')

    def __str__(self):
        return f'Pago #{self.id} - Orden #{self.orden.id}'

    def calcular_bs(self):
        """Si se proporciona la tasa, calcula monto en Bs automáticamente"""
        if self.monto_usd and self.tasa_cambio:
            self.monto_bs = self.monto_usd * self.tasa_cambio
