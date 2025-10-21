from rest_framework import serializers
from .models import Wallet, Movimiento


class MovimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movimiento
        fields = ['id', 'tipo', 'monto', 'descripcion', 'creado_en']
        read_only_fields = ['wallet', 'creado_en']

class WalletSerializer(serializers.ModelSerializer):

    movimientos = MovimientoSerializer(many=True, read_only=True)
    class Meta:
        model = Wallet
        fields = ['id', 'saldo', 'movimientos']
        read_only_fields = ['usuario', 'saldo']

