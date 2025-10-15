
# notificaciones/utils.py
from .models import Notificacion

def enviar_notificacion(usuario, titulo, mensaje):
    Notificacion.objects.create(
        usuario=usuario,
        titulo=titulo,
        mensaje=mensaje
    )
