from rest_framework import viewsets, permissions, status
from .models import Wallet, Movimiento
from .serializers import WalletSerializer, MovimientoSerializer
from rest_framework.decorators import action
from rest_framework.response import Response

class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.rol.nombre == 'admin':
            return Wallet.objects.all()
        elif user.rol.nombre in ['conductor', 'comercio']:
            return Wallet.objects.filter(usuario=user)
        return Wallet.objects.none()

    @action(detail=False, methods=['post'])
    def create_wallet(self, request):
        user = request.user

        # Solo roles válidos pueden crear wallet
        if user.rol.nombre not in ['conductor', 'comercio', 'admin']:
            return Response({"error": "No tienes permisos para crear wallet."}, status=status.HTTP_403_FORBIDDEN)

        # Verificar si ya tiene wallet
        if Wallet.objects.filter(usuario=user).exists():
            return Response({"error": "Ya tienes una wallet."}, status=status.HTTP_400_BAD_REQUEST)

        # Crear la wallet
        wallet = Wallet.objects.create(usuario=user, saldo=0.0)
        serializer = WalletSerializer(wallet)
        return Response({"success": True, "wallet": serializer.data}, status=status.HTTP_201_CREATED)


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


