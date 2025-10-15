from django.shortcuts import render

# Create your views here.
# calificaciones/views.py
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Calificacion
from .serializers import CalificacionSerializer
from auditoria.services import registrar_auditoria  # Asegúrate que esto esté en utils.py
from core.permissions import IsCliente

class CalificacionViewSet(viewsets.ModelViewSet):
    queryset = Calificacion.objects.all()
    serializer_class = CalificacionSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [permissions.IsAuthenticated(), IsCliente()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.rol.nombre == 'cliente':
            return Calificacion.objects.filter(cliente=user)
        elif user.rol.nombre == 'admin':
            return Calificacion.objects.all()
        return Calificacion.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if serializer.validated_data['orden'].cliente != user:
            raise PermissionDenied("No puedes calificar una orden que no es tuya.")
        calificacion = serializer.save(cliente=user)
        registrar_auditoria(
            usuario=self.request.user,
            accion='crear',
            descripcion=f'Creó una calificación de {calificacion.puntaje} puntos.',
            modelo_afectado='Calificacion',
            id_objeto=calificacion.id
        )

    def perform_update(self, serializer):
        calificacion = serializer.save()
        registrar_auditoria(
            usuario=self.request.user,
            accion='actualizar',
            descripcion=f'Actualizó la calificación #{calificacion.id}',
            modelo_afectado='Calificacion',
            id_objeto=calificacion.id
        )
