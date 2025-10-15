# restaurantes/serializers.py

from rest_framework import serializers
from .models import Restaurante, EstadoRestaurante, CategoriaRestaurante, OpcionPlato, TipoOpcion
from .models import Plato

class EstadoRestauranteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoRestaurante
        fields = '__all__'


class CategoriaRestauranteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaRestaurante
        fields = ['id', 'nombre', 'imagen']

        
class RestauranteSerializer(serializers.ModelSerializer):
    categoria = CategoriaRestauranteSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
    queryset=CategoriaRestaurante.objects.all(),
    source='categoria',
    write_only=True,
    required=False,
    allow_null=True
)

    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = Restaurante
        fields = '__all__'
        read_only_fields = ['usuario', 'calificacion_promedio']

    def get_imagen_url(self, obj):
        request = self.context.get('request')
        if obj.imagen:
            return request.build_absolute_uri(obj.imagen.url)
        return None


class OpcionPlatoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpcionPlato
        fields = ['id', 'nombre', 'precio_adicional', 'disponible']


class TipoOpcionSerializer(serializers.ModelSerializer):
    opciones = OpcionPlatoSerializer(many=True, read_only=True)

    class Meta:
        model = TipoOpcion
        fields = ['id', 'nombre', 'obligatorio', 'multiple', 'opciones', 'plato']


class PlatoSerializer(serializers.ModelSerializer):
    imagen_url = serializers.SerializerMethodField()
    restaurante_nombre = serializers.CharField(source="restaurante.nombre", read_only=True)
    calificacion_promedio = serializers.SerializerMethodField(read_only=True)
    tipos_opciones = TipoOpcionSerializer(many=True, read_only=True)  # ← Cambiado

    class Meta:
        model = Plato
        fields = ['id', 'nombre', 'descripcion', 'precio', 'imagen','imagen_url' ,'disponible', 'restaurante', 'restaurante_nombre', 'precio_descuento', 'calificacion_promedio', 'tipos_opciones']
        read_only_fields = ['restaurante']

        

    def get_imagen_url(self, obj):
        if obj.imagen:
            # Devuelve solo la ruta relativa (sin la URL completa)
            return obj.imagen.name  # ejemplo: 'platos/dc0a8872-f808-4613-8a27-e7b3b4100bbb.jpeg'
        return None
    
    def get_calificacion_promedio(self, obj):
        return getattr(obj.restaurante, "calificacion_promedio", 0)

    def update(self, instance, validated_data):
        if 'imagen' in validated_data:
            if validated_data['imagen'] is None:
                instance.imagen.delete(save=False)
        else:
            validated_data['imagen'] = instance.imagen
        return super().update(instance, validated_data)

