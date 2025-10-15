from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Pago, MetodoPago
from .serializers import PagoSerializer, MetodoPagoSerializer
from auditoria.services import registrar_auditoria
from .utils import verificacion_pago


class MetodoPagoViewSet(viewsets.ModelViewSet):
    queryset = MetodoPago.objects.all()
    serializer_class = MetodoPagoSerializer
    permission_classes = [permissions.IsAuthenticated]


class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.rol.nombre == "admin":
            return Pago.objects.all()
        return Pago.objects.filter(usuario=user)

    def perform_create(self, serializer):
        user = self.request.user
        pago = serializer.save(usuario=user)

        # Si es pago móvil → verificar en banco
        if pago.metodo.nombre.lower() == "pago móvil":
            verificacion_pago(pago)
        else:
            # Otros métodos se confirman de una vez
            pago.confirmado = True
            pago.save(update_fields=["confirmado"])

        registrar_auditoria(
            usuario=user,
            accion='crear',
            descripcion=f'Realizó un pago de {pago.monto_usd} USD para la orden #{pago.orden.id}',
            modelo_afectado='Pago'
        )

    def perform_update(self, serializer):
        pago = self.get_object()
        user = self.request.user

        confirmado_nuevo = self.request.data.get("confirmado", None)
        if confirmado_nuevo is not None and str(confirmado_nuevo).lower() != str(pago.confirmado).lower():
            if user.rol.nombre != "comercio":
                raise PermissionDenied("Solo los usuarios con rol comercio pueden confirmar pagos.")

        pago_actualizado = serializer.save()

        registrar_auditoria(
            usuario=user,
            accion="actualizar",
            descripcion=f"Actualizó el pago #{pago_actualizado.id}",
            modelo_afectado="Pago",
        )

    def perform_destroy(self, instance):
        registrar_auditoria(
            usuario=self.request.user,
            accion="eliminar",
            descripcion=f"Eliminó el pago #{instance.id}",
            modelo_afectado="Pago",
        )
        instance.delete()
