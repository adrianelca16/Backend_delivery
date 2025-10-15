# auditoria/services.py
from .models import Auditoria

def registrar_auditoria(usuario, accion, descripcion, modelo_afectado=None, objeto_id=None):
    Auditoria.objects.create(
        usuario=usuario,
        accion=accion,
        descripcion=descripcion,
        modelo_afectado=modelo_afectado,
        objeto_id=objeto_id
    )
