from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Usuario, Conductor, Rol

@receiver(post_save, sender=Usuario)
def crear_conductor_si_es_rol_conductor(sender, instance, created, **kwargs):
    if created and instance.rol.nombre.lower() == "conductor":
        # Crear conductor solo si no existe
        Conductor.objects.get_or_create(usuario=instance)
