# auditoria/models.py
from django.db import models
from django.utils.timezone import now
from core.models import Usuario
import uuid

class Auditoria(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=100)
    descripcion = models.TextField()
    modelo_afectado = models.CharField(max_length=100, null=True, blank=True)
    objeto_id = models.CharField(max_length=100, null=True, blank=True)
    fecha = models.DateTimeField(default=now)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"{self.accion} - {self.usuario} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"
