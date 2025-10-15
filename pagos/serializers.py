from rest_framework import serializers
from .models import Pago, MetodoPago

class MetodoPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetodoPago
        fields = '__all__'
        
class PagoSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.ReadOnlyField(source="usuario.nombre")
    metodo_nombre = serializers.ReadOnlyField(source="metodo.nombre")

    class Meta:
        model = Pago
        fields = [
            "id",
            "orden",
            "usuario",
            "usuario_nombre",
            "metodo",
            "metodo_nombre",
            "monto_usd",
            "monto_bs",
            "tasa_cambio",
            "confirmado",
            "creado_en",
            "referencia",
            'telefono_pago'
        ]
        read_only_fields = ["usuario", "confirmado", "creado_en", "monto_bs"]

    def validate(self, data):
        orden = data.get("orden")
        metodo = data.get("metodo")

        if Pago.objects.filter(orden=orden, metodo=metodo).exists():
            raise serializers.ValidationError(
                "Ya existe un pago registrado para esta orden con este método."
            )

        return data

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        validated_data["usuario"] = user

        # Calcular monto en Bs si se pasa tasa
        tasa = validated_data.get("tasa_cambio")
        monto_usd = validated_data.get("monto_usd")
        if tasa and monto_usd:
            validated_data["monto_bs"] = monto_usd * tasa

        pago = super().create(validated_data)

        # Confirmar automáticamente si no es pago móvil
        metodo = pago.metodo.nombre.strip().lower()
        if metodo != "pago movil":
            pago.confirmado = True
            pago.save(update_fields=["confirmado"])

        return pago

