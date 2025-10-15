from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import UbicacionConductor
from .serializers import UbicacionConductorSerializer
from core.permissions import IsConductor
from auditoria.services import registrar_auditoria


class UbicacionConductorViewSet(viewsets.ModelViewSet):
    queryset = UbicacionConductor.objects.all()
    serializer_class = UbicacionConductorSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [permissions.IsAuthenticated(), IsConductor()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        if self.request.user.rol.nombre != 'conductor':
            raise PermissionDenied("Solo los conductores pueden crear su ubicación.")
        serializer.save(conductor=self.request.user)

        registrar_auditoria(
            usuario=self.request.user,
            accion="Ubicación actualizada",
            descripcion=f"Ubicación del conductor actualizada",
            modelo_afectado='UbicacionConductor',
            objeto_id=ubicacion.id
        )

    def get_queryset(self):
        user = self.request.user
        if user.rol.nombre == 'admin':
            return UbicacionConductor.objects.all()
        return UbicacionConductor.objects.filter(conductor=user)
