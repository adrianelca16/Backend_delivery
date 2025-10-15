from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Usuario, Rol, Direccion, Conductor, CodigoVerificacion
from .serializers import RegisterSerializer, RolSerializer, DireccionSerializer, UsuarioUpdateSerializer, ConductorSerializer
from django.contrib.auth import authenticate
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework import permissions
import random
import requests

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "Usuario creado correctamente"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(email=email, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)

            foto_url = None
            if user.foto_perfil and hasattr(user.foto_perfil, "url"):
                foto_url = request.build_absolute_uri(user.foto_perfil.url)


            return Response({
                "token": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "usuario": {
                    "id": user.id,
                    "email": user.email,
                    "rol": user.rol.nombre,
                    "nombre": user.nombre,
                    "telefono": user.telefono,
                    "foto_perfil": foto_url,
                }
            })
        return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

class RolViewSet(viewsets.ReadOnlyModelViewSet):  # Solo lectura
    queryset = Rol.objects.exclude(nombre__iexact="admin")
    serializer_class = RolSerializer
    permission_classes = [permissions.AllowAny]

class DireccionViewSet(viewsets.ModelViewSet):
    serializer_class = DireccionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Cada usuario solo puede ver sus direcciones
        return Direccion.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        # Si la nueva dirección viene como predeterminada, desmarcar las otras
        if serializer.validated_data.get("es_predeterminada", False):
            Direccion.objects.filter(
                usuario=self.request.user, es_predeterminada=True
            ).update(es_predeterminada=False)

        # Al crear una dirección, se asigna el usuario autenticado
        serializer.save(usuario=self.request.user)

    def perform_update(self, serializer):
        # Si se actualiza a predeterminada, desmarcar las otras
        if serializer.validated_data.get("es_predeterminada", False):
            Direccion.objects.filter(
                usuario=self.request.user, es_predeterminada=True
            ).exclude(pk=serializer.instance.pk).update(es_predeterminada=False)

        serializer.save()

EMAIL_WEBHOOK_URL = "https://cloverwebhook.clovercube.shop/webhook/email-delivery-express"
WHATSAPP_WEBHOOK_URL = "https://cloverwebhook.clovercube.shop/webhook/whats-app-deliver-express"


class UsuarioViewSet(viewsets.ModelViewSet):
    serializer_class = UsuarioUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        return Usuario.objects.filter(id=self.request.user.id)

    def get_object(self):
        return self.request.user
    
    @action(detail=False, methods=['post'], url_path='enviar-codigo')
    def enviar_codigo(self, request):
        usuario = request.user
        metodo = request.data.get('metodo')

        if metodo not in ['email', 'telefono']:
            return Response({'error': 'Método inválido'}, status=status.HTTP_400_BAD_REQUEST)

        # 1️⃣ Generar código aleatorio de 6 dígitos
        codigo = str(random.randint(100000, 999999))

        # 2️⃣ Guardarlo en la base de datos
        CodigoVerificacion.objects.create(
            usuario=usuario,
            codigo=codigo,
            metodo=metodo
        )

        try:
            # 3️⃣ Enviar a la API correspondiente
            if metodo == 'email':
                payload = {
                    "destinatario": usuario.email,
                    "desde": "adrian.elca15@mail.com",
                    "codigo": codigo,
                    "asunto": "Verificación de Correo Electrónico",
                    "mensaje": "Usá el siguiente código para completar tu verificación en la app (DeliveryExpress):"
                }
                requests.post(EMAIL_WEBHOOK_URL, json=payload, timeout=10)

            elif metodo == 'telefono':
                payload = {
                    "destinatario": usuario.telefono,
                    "mensaje": codigo,
                    "instancia": "Feldvic",
                    "nombre": usuario.nombre
                }
                requests.post(WHATSAPP_WEBHOOK_URL, json=payload, timeout=10)

            return Response({
                "mensaje": f"Código enviado correctamente por {metodo}.",
                "codigo_prueba": codigo  # ⚠️ solo para desarrollo
            })

        except Exception as e:
            return Response({
                "error": f"Error al enviar código: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='verificar-codigo')
    def verificar_codigo(self, request):
        metodo = request.data.get('metodo')
        codigo = request.data.get('codigo')
        usuario = request.user

        try:
            codigo_obj = CodigoVerificacion.objects.filter(
                usuario=usuario,
                metodo=metodo,
                codigo=codigo,
                usado=False
            ).latest('creado_en')
        except CodigoVerificacion.DoesNotExist:
            return Response({'error': 'Código inválido'}, status=status.HTTP_400_BAD_REQUEST)

        if not codigo_obj.es_valido():
            return Response({'error': 'Código expirado o ya usado'}, status=status.HTTP_400_BAD_REQUEST)

        # Marcar como usado
        codigo_obj.usado = True
        codigo_obj.save()

        # Activar verificación
        if metodo == 'email':
            usuario.verificacion_email = True
        elif metodo == 'telefono':
            usuario.verificacion_telefono = True

        usuario.save()

        return Response({'mensaje': f'{metodo} verificado correctamente'})



class ConductorViewSet(viewsets.ModelViewSet):
    queryset = Conductor.objects.all()
    serializer_class = ConductorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.rol.nombre.lower() == "conductor":
            # conductor solo puede ver su propio perfil
            return Conductor.objects.filter(usuario=user)

        if user.rol.nombre.lower() == "admin":
            return Conductor.objects.all()

        # por defecto, no muestra nada
        return Conductor.objects.none()

    @action(detail=False, methods=["get"])
    def disponibles(self, request):
        disponibles = Conductor.objects.filter(
            disponible=True,
            suspendido_hasta__isnull=True
        ).order_by("ultimo_pedido")
        serializer = self.get_serializer(disponibles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get", "patch"])
    def mi_estado(self, request):
        """GET = ver estado, PATCH = actualizar estado"""
        user = request.user
        if not hasattr(user, "conductor"):
            return Response({"detail": "No eres un conductor"}, status=400)

        conductor = user.conductor

        # PATCH -> actualizar estado
        if request.method == "PATCH":
            serializer = self.get_serializer(
                conductor, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        # GET -> mostrar estado
        serializer = self.get_serializer(conductor)
        return Response(serializer.data)
    
    
    @action(detail=False, methods=["post"])
    def registrar_token(request):
        user = request.user
        token = request.data.get("token")

        if not token:
            return Response({"detail": "Token requerido"}, status=status.HTTP_400_BAD_REQUEST)

        if hasattr(user, "conductor"):
            user.conductor.push_token = token
            user.conductor.save()
            return Response({"detail": "Token registrado"}, status=status.HTTP_200_OK)

        return Response({"detail": "El usuario no es conductor"}, status=status.HTTP_400_BAD_REQUEST)
    
   