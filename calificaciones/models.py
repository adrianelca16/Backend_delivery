# calificaciones/models.py
from django.db import models
from core.models import Usuario
from ordenes.models import Orden
import uuid

class Calificacion(models.Model):
    orden = models.OneToOneField(Orden, on_delete=models.CASCADE, related_name='calificacion')
    cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE, limit_choices_to={'rol__nombre': 'cliente'})
    conductor_puntaje = models.PositiveSmallIntegerField(null=True, blank=True)
    restaurante_puntaje = models.PositiveSmallIntegerField(null=True, blank=True)
    comentario = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"Calificación de {self.cliente} para orden #{self.orden.id}"
