from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Usuario
from .models import Wallet

@receiver(post_save, sender=Usuario)
def crear_wallet(sender, instance, created, **kwargs):
    if created and instance.rol.nombre == 'conductor':
        Wallet.objects.get_or_create(usuario=instance)
