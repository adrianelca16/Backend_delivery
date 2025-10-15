from django.db import models
from core.models import Usuario
import uuid

class UbicacionConductor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conductor = models.OneToOneField(Usuario, on_delete=models.CASCADE, limit_choices_to={'rol__nombre': 'conductor'})
    latitud = models.FloatField()
    longitud = models.FloatField()
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ubicación de {self.conductor.nombre}"
