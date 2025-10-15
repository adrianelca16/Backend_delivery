from rest_framework import serializers
from .models import Wallet, Movimiento

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'usuario', 'saldo']
        read_only_fields = ['usuario', 'saldo']

class MovimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movimiento
        fields = ['id', 'tipo', 'monto', 'descripcion', 'creado_en']
        read_only_fields = ['wallet', 'creado_en']
