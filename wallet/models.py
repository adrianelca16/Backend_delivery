from django.db import models
from django.utils import timezone
from core.models import Usuario
import uuid

class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='wallet')
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    

    def __str__(self):
        return f"Wallet de {self.usuario.nombre} - {self.saldo}"


class Movimiento(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    TIPO_CHOICES = [
        ('ingreso', 'Ingreso por orden'),
        ('retiro', 'Pago retirado'),
        ('ajuste', 'Ajuste manual'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True)
    creado_en = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.tipo} - {self.monto} - {self.wallet.usuario}"
