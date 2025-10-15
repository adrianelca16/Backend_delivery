from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import uuid, os
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class Rol(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()
    icons = models.CharField(max_length=100, blank=True, null=True)  # Icono opcional

    def __str__(self):
        return self.nombre


class EstadoUsuario(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre


def usuario_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('usuarios', filename)

class Usuario(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT)
    estado = models.ForeignKey(EstadoUsuario, on_delete=models.PROTECT)
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    telefono = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?\d{10,15}$', "El teléfono debe tener entre 10 y 15 dígitos, con opción de +")]
    )
    
    foto_perfil = models.ImageField(upload_to=usuario_image_path, blank=True, null=True)
    cedula_imagen = models.ImageField(upload_to=usuario_image_path, blank=True, null=True)

    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    cedula_imagen = models.ImageField(upload_to=usuario_image_path, blank=True, null=True)

    verificacion_email = models.BooleanField(default=False, blank=True, null=True)
    verificacion_telefono = models.BooleanField(default=False, blank=True, null=True)
    verificacion_identidad = models.BooleanField(default=False, blank=True, null=True)

    verificacion_intentos = models.IntegerField(default=0)
    comentarios_verificacion = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        try:
            old_instance = Usuario.objects.get(pk=self.pk)
            if old_instance.foto_perfil and self.foto_perfil and self.foto_perfil != old_instance.foto_perfil:
                old_path = os.path.join(settings.MEDIA_ROOT, str(old_instance.foto_perfil))
                if os.path.exists(old_path):
                    os.remove(old_path)
        except Usuario.DoesNotExist:
            pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.foto_perfil:
            foto_path = os.path.join(settings.MEDIA_ROOT, str(self.foto_perfil))
            if os.path.exists(foto_path):
                os.remove(foto_path)
        super().delete(*args, **kwargs)

class Direccion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='direcciones')
    direccion_texto = models.CharField(max_length=255)
    latitud = models.FloatField()
    longitud = models.FloatField()
    es_predeterminada = models.BooleanField(default=False)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.usuario.nombre} - {self.direccion_texto}"

class Conductor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name="conductor"
    )
    disponible = models.BooleanField(default=False)
    ultimo_pedido = models.DateTimeField(null=True, blank=True)
    penitencias = models.IntegerField(default=0)
    ultima_penitencia = models.DateTimeField(null=True, blank=True)
    suspendido_hasta = models.DateTimeField(null=True, blank=True)
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)
    push_token = models.CharField(max_length=255, null=True, blank=True)

    def registrar_penitencia(self):
        """Suma una penitencia y evalúa sanción."""
        from django.utils import timezone
        from datetime import timedelta

        self.penitencias += 1
        self.ultima_penitencia = timezone.now()
        self.save()

        if self.penitencias >= 3 and self.en_ultima_semana():
            self.sancionar()

    def en_ultima_semana(self):
        """Revisa si las penitencias son recientes."""
        from django.utils import timezone
        from datetime import timedelta

        if not self.ultima_penitencia:
            return False
        return self.ultima_penitencia >= timezone.now() - timedelta(days=7)

    def sancionar(self):
        """Aplica sanción: suspensión 7 días, por ejemplo."""
        from django.utils import timezone
        from datetime import timedelta

        self.suspendido_hasta = timezone.now() + timedelta(days=7)
        self.disponible = False
        self.save()

    def __str__(self):
        return f"Conductor {self.usuario.nombre}"

class CodigoVerificacion(models.Model):
    METODO_CHOICES = [
        ('email', 'Correo Electrónico'),
        ('telefono', 'Teléfono'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='codigos_verificacion')
    codigo = models.CharField(max_length=6)
    metodo = models.CharField(max_length=10, choices=METODO_CHOICES)
    creado_en = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)

    def es_valido(self):
        """Retorna True si el código sigue vigente (5 minutos)"""
        return timezone.now() < self.creado_en + timedelta(minutes=5) and not self.usado

    def __str__(self):
        return f"{self.usuario.email} - {self.metodo} - {self.codigo}"