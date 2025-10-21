from rest_framework import serializers
from .models import EstadoOrden, Orden, DetalleOrden
from core.models import Usuario
from restaurantes.serializers import OpcionPlatoSerializer  

class EstadoOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoOrden
        fields = '__all__'


class DetalleOrdenSerializer(serializers.ModelSerializer):
    plato_nombre = serializers.ReadOnlyField(source='plato.nombre')
    plato_imagen = serializers.SerializerMethodField()

     # 👇 Este campo solo se usa cuando llega el JSON desde el frontend
    extras = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        write_only=True  # 🔥 solo escritura
    )

    # 👇 Este se usa para devolver los extras al frontend
    extras_detalle = OpcionPlatoSerializer(source='extras', many=True, read_only=True)


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
            'extras',
            'extras_detalle',
        ]
        read_only_fields = ['precio_unitario', 'subtotal', 'descuento', 'extras_detalle']

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

        for detalle_data in detalles_data:
            extras_data = detalle_data.pop('extras', [])
            detalle = DetalleOrden.objects.create(orden=orden, **detalle_data)

            # 🧩 Procesar extras
            extras_ids = []
            for extra_obj in extras_data:
                extra_id = extra_obj.get('id')
                if extra_id:
                    extras_ids.append(extra_id)

            if extras_ids:
                detalle.extras.set(extras_ids)
                detalle.save()  # recalcula subtotal con extras

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