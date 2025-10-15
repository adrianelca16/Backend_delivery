from rest_framework import serializers
from .models import Usuario, Rol, Direccion, Conductor,EstadoUsuario
from .utils import validar_identidad_con_gpt

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    rol = serializers.PrimaryKeyRelatedField(queryset=Rol.objects.all()) 

    class Meta:
        model = Usuario
        fields = ['email', 'password', 'nombre', 'telefono', 'foto_perfil', 'rol', ]

    def create(self, validated_data):
        try:
            estado_activo = EstadoUsuario.objects.get(nombre="activo")  
        except EstadoUsuario.DoesNotExist:
            raise serializers.ValidationError("El estado 'Activo' no está configurado en la base de datos.")

        validated_data['estado'] = estado_activo
        return Usuario.objects.create_user(**validated_data)


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id', 'nombre', 'descripcion', 'icons']

class DireccionSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source="usuario.nombre", read_only=True)

    class Meta:
        model = Direccion
        fields = [
            'id',
            'usuario',
            'usuario_nombre',
            'nombre',
            'direccion_texto',
            'latitud',
            'longitud',
            'es_predeterminada',
        ]
        read_only_fields = ['usuario']

class UsuarioUpdateSerializer(serializers.ModelSerializer):
    foto_perfil_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Usuario
        fields = ['nombre', 'telefono', 'email', 'foto_perfil', 'foto_perfil_url', 'verificacion_email', 'verificacion_telefono', 'verificacion_identidad', 'cedula_imagen']

    def get_foto_perfil_url(self, obj):
        request = self.context.get("request")
        if obj.foto_perfil and hasattr(obj.foto_perfil, "url"):
            return request.build_absolute_uri(obj.foto_perfil.url)
        return None

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        if instance.foto_perfil and instance.cedula_imagen and not instance.verificacion_identidad:
            
            es_valido, mensaje = validar_identidad_con_gpt(
                instance.foto_perfil.path,
                instance.cedula_imagen.path
            )

            instance.verificacion_identidad = es_valido
            instance.comentarios_verificacion = mensaje
            instance.verificacion_intentos += 1
            instance.save()

        return instance

    

class ConductorSerializer(serializers.ModelSerializer):
    usuario = UsuarioUpdateSerializer(read_only=True)  # para mostrar los datos del usuario
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        source="usuario",
        write_only=True
    )

    class Meta:
        model = Conductor
        fields = [
            "id",
            "usuario",        # datos anidados de usuario
            "usuario_id",     # para crear/editar relacion
            "disponible",
            "ultimo_pedido",
            "penitencias",
            "ultima_penitencia",
            "suspendido_hasta",
            'latitud',
            'longitud',
        ]
        read_only_fields = ["penitencias", "ultima_penitencia", "suspendido_hasta"]
    
    def validate_usuario(self, value):
        if value.rol.nombre.lower() != "conductor":
            raise serializers.ValidationError("El usuario no tiene rol de conductor.")
        return value
