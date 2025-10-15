from rest_framework import serializers
from .models import EstadoOrden, Orden, DetalleOrden
from core.models import Usuario

class EstadoOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoOrden
        fields = '__all__'


class DetalleOrdenSerializer(serializers.ModelSerializer):
    plato_nombre = serializers.ReadOnlyField(source='plato.nombre')
    plato_imagen = serializers.SerializerMethodField()

    class Meta:
        model = DetalleOrden
        fields = [
            'id',
            'plato',
            'plato_nombre',
            'plato_imagen',
            'cantidad',
            'precio_unitario',
            'subtotal',
            'descuento',
        ]
        read_only_fields = ['precio_unitario', 'subtotal', 'descuento']

    def get_plato_imagen(self, obj):
        print("DEBUG imagen plato:", obj.plato.imagen)  # <- aquí sí
        request = self.context.get('request')
        if obj.plato.imagen:
            return request.build_absolute_uri(obj.plato.imagen.url)
        return None

class OrdenSerializer(serializers.ModelSerializer):
    detalles = DetalleOrdenSerializer(many=True, required=False)
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    restaurante_nombre = serializers.ReadOnlyField(source='restaurante.nombre')
    estado_nombre = serializers.ReadOnlyField(source='estado.nombre')
    restaurante_imagen = serializers.SerializerMethodField()
    cliente_email = serializers.ReadOnlyField(source="cliente.email")
    cliente_telefono = serializers.ReadOnlyField(source="cliente.telefono")
    cliente_foto = serializers.SerializerMethodField()
    costo_envio = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    

    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(rol__nombre='cliente'),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Orden
        fields = [
            'id',
            'cliente',
            'cliente_nombre',
            'restaurante',
            'restaurante_nombre',
            'conductor',
            'estado',
            'estado_nombre',
            'metodo_pago',
            'subtotal',
            'descuento',
            'impuesto',
            'total',
            'detalles',
            'creado_en',
            'actualizado_en',
            'numero_orden',
            'direccion_entrega',
            'latitud',
            'longitud',
            'restaurante_imagen',
            "cliente_email",
            "cliente_telefono",
            "cliente_foto",
            'costo_envio',
        ]
        read_only_fields = ['subtotal', 'descuento', 'impuesto', 'total','numero_orden']

    def validate(self, data):
        user = self.context['request'].user
        cliente = data.get('cliente')

        if user.rol.nombre == 'cliente' and cliente and cliente != user:
            raise serializers.ValidationError("Un cliente solo puede crear órdenes para sí mismo.")

        return data

    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles', [])
        orden = Orden.objects.create(**validated_data)

        for detalle in detalles_data:
            DetalleOrden.objects.create(orden=orden, **detalle)

        orden.calcular_total()
        return orden
    
    def get_restaurante_imagen(self, obj):
        request = self.context.get("request")
        if obj.restaurante.imagen:
            return request.build_absolute_uri(obj.restaurante.imagen.url)
        return None
    
    def get_cliente_foto(self, obj):
        request = self.context.get("request")
        if obj.cliente and obj.cliente.foto_perfil:
            return request.build_absolute_uri(obj.cliente.foto_perfil.url)
        return None