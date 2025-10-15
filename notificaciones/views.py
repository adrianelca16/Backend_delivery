from django.shortcuts import render

# Create your views here.
# notificaciones/views.py
from rest_framework import viewsets, permissions
from .models import Notificacion
from .serializers import NotificacionSerializer
from auditoria.services import registrar_auditoria

class NotificacionViewSet(viewsets.ModelViewSet):
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notificacion.objects.filter(usuario=self.request.user).order_by('-creada_en')

    def perform_create(self, serializer):
        notificacion = serializer.save(usuario=self.request.user)
        registrar_auditoria(
            usuario=self.request.user,
            accion='crear',
            descripcion=f'Creó una notificación: "{notificacion.titulo}"',
            modelo_afectado='Notificacion',
            id_objeto=notificacion.id
        )
