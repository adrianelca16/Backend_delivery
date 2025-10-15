from django.db import models
from core.models import Usuario
import uuid
import os
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class EstadoRestaurante(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.nombre

import uuid
import os
from django.conf import settings

def categoria_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('categorias', filename)

class CategoriaRestaurante(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    imagen = models.ImageField(upload_to=categoria_image_path, null=True, blank=True)

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        try:
            old_instance = CategoriaRestaurante.objects.get(pk=self.pk)
            if old_instance.imagen and self.imagen and self.imagen != old_instance.imagen:
                old_path = os.path.join(settings.MEDIA_ROOT, str(old_instance.imagen))
                if os.path.exists(old_path):
                    os.remove(old_path)
        except CategoriaRestaurante.DoesNotExist:
            pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.imagen:
            imagen_path = os.path.join(settings.MEDIA_ROOT, str(self.imagen))
            if os.path.exists(imagen_path):
                os.remove(imagen_path)
        super().delete(*args, **kwargs)

def restaurante_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('restaurante', filename)

class Restaurante(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    direccion = models.CharField(max_length=255)
    latitud = models.FloatField()
    longitud = models.FloatField()
    horario_apertura = models.TimeField()  # Cambié a TimeField para mejor manejo
    horario_cierre = models.TimeField()
    calificacion_promedio = models.FloatField(default=0)
    estado = models.ForeignKey(EstadoRestaurante, on_delete=models.CASCADE)
    categoria = models.ForeignKey(CategoriaRestaurante, on_delete=models.SET_NULL, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    pagina_web = models.URLField(null=True, blank=True)
    capacidad = models.PositiveIntegerField(null=True, blank=True)
    imagen = models.ImageField(upload_to=restaurante_image_path, null=True, blank=True)
    banner = models.ImageField(upload_to='restaurantes/banners/', null=True, blank=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.nombre

    def esta_abierto(self):
        """Devuelve True si el restaurante está abierto en el momento actual."""
        ahora = timezone.localtime().time()
        if self.horario_apertura < self.horario_cierre:
            # horario normal, por ejemplo 9:00 - 21:00
            return self.horario_apertura <= ahora <= self.horario_cierre
        else:
            # horario cruzando medianoche, ejemplo 20:00 - 4:00
            return ahora >= self.horario_apertura or ahora <= self.horario_cierre
    
    def save(self, *args, **kwargs):
        if self.pk:  # Solo intenta obtener la instancia si ya existe (actualización)
            try:
                old_instance = Restaurante.objects.get(pk=self.pk)
                if old_instance.imagen and self.imagen and self.imagen != old_instance.imagen:
                    old_path = os.path.join(settings.MEDIA_ROOT, str(old_instance.imagen))
                    if os.path.exists(old_path):
                        os.remove(old_path)
            except Restaurante.DoesNotExist:  # 👈 Corregido
                pass

        super().save(*args, **kwargs)


    def delete(self, *args, **kwargs):
        if self.imagen:
            imagen_path = os.path.join(settings.MEDIA_ROOT, str(self.imagen))
            if os.path.exists(imagen_path):
                os.remove(imagen_path)
        super().delete(*args, **kwargs)
    

def plato_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('platos', filename)

class Plato(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurante = models.ForeignKey('Restaurante', on_delete=models.CASCADE, related_name='platos')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.ImageField(upload_to=plato_image_path, blank=True, null=True)
    disponible = models.BooleanField(default=True)
    precio_descuento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        try:
            old_instance = Plato.objects.get(pk=self.pk)
            if old_instance.imagen and self.imagen and self.imagen != old_instance.imagen:
                old_path = os.path.join(settings.MEDIA_ROOT, str(old_instance.imagen))
                if os.path.exists(old_path):
                    os.remove(old_path)
        except Plato.DoesNotExist:
            pass
        super().save(*args, **kwargs)


    def delete(self, *args, **kwargs):
        if self.imagen:
            imagen_path = os.path.join(settings.MEDIA_ROOT, str(self.imagen))
            if os.path.exists(imagen_path):
                os.remove(imagen_path)
        super().delete(*args, **kwargs)

class TipoOpcion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurante = models.ForeignKey(
        'Restaurante',
        on_delete=models.CASCADE,
        related_name='tipos_opciones'
    )
    plato = models.ForeignKey(
        'Plato',
        on_delete=models.CASCADE,
        related_name='tipos_opciones',
        null=True, blank=True   # 👈 añade esto
    )
    nombre = models.CharField(max_length=100)
    obligatorio = models.BooleanField(default=False)
    multiple = models.BooleanField(default=False)


class OpcionPlato(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.ForeignKey(
        'TipoOpcion',
        on_delete=models.CASCADE,
        related_name='opciones'
    )
    nombre = models.CharField(max_length=100)
    precio_adicional = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} (+{self.precio_adicional})"