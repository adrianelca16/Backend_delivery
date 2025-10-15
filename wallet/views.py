from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Wallet, Movimiento
from .serializers import WalletSerializer, MovimientoSerializer

class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.rol.nombre == 'admin':
            return Wallet.objects.all()
        elif user.rol.nombre == 'conductor':
            return Wallet.objects.filter(usuario=user)
        return Wallet.objects.none()


class MovimientoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MovimientoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.rol.nombre == 'admin':
            return Movimiento.objects.all()
        elif user.rol.nombre == 'conductor':
            return Movimiento.objects.filter(wallet=user.wallet)
        return Movimiento.objects.none()
