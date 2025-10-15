# restaurantes/views.py

from rest_framework import viewsets, permissions
from .models import Restaurante, EstadoRestaurante, Plato, CategoriaRestaurante, TipoOpcion, OpcionPlato
from .serializers import RestauranteSerializer, EstadoRestauranteSerializer, PlatoSerializer, CategoriaRestauranteSerializer, OpcionPlatoSerializer, TipoOpcionSerializer
from core.permissions import IsComercio
from rest_framework.exceptions import PermissionDenied
from auditoria.services import registrar_auditoria
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404


class EstadoRestauranteViewSet(viewsets.ModelViewSet):
    queryset = EstadoRestaurante.objects.all()
    serializer_class = EstadoRestauranteSerializer
    permission_classes = [permissions.AllowAny]

class CategoriasRestauranteViewSet(viewsets.ModelViewSet):
    queryset = CategoriaRestaurante.objects.all()
    serializer_class = CategoriaRestauranteSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = (MultiPartParser, FormParser)


class RestauranteViewSet(viewsets.ModelViewSet):
    queryset = Restaurante.objects.none()
    serializer_class = RestauranteSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)  # para soportar imagen

    def get_queryset(self):
        user = self.request.user
        rol_nombre = getattr(user.rol, "nombre", None)
        print("DEBUG → usuario:", user.email, "rol:", rol_nombre)

        if user.is_staff:
            return Restaurante.objects.all()
        if rol_nombre == "cliente":
            return Restaurante.objects.all()
        if rol_nombre == "comercio":
            return Restaurante.objects.filter(usuario=user)

        return Restaurante.objects.none()



    def get_permissions(self):
        if self.action == 'create':
            return [IsComercio()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        elif self.action == 'list':
            return [permissions.IsAuthenticated()]
        elif self.action == 'mi_restaurante':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
    
        user = request.user

        # Si es staff → todo ok
        if user.is_staff:
            pass
        # Si es comercio → solo su restaurante
        elif hasattr(user, "rol") and user.rol == "comercio":
            if instance.usuario != user:
                return Response({'detail': 'No tienes permiso para ver este restaurante.'}, status=403)
        # Si es cliente → puede ver cualquiera (no hacemos nada)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get', 'put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def mi_restaurante(self, request):
        restaurante = Restaurante.objects.filter(usuario=request.user).first()
        if not restaurante:
            return Response(None, status=200)

        if request.method in ['PUT', 'PATCH']:
            serializer = self.get_serializer(
                restaurante,
                data=request.data,
                partial=(request.method == 'PATCH')  # Permite actualizaciones parciales
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=200)

        serializer = self.get_serializer(restaurante)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def platos(self, request, pk=None):
        restaurante = self.get_object()
        # Usa el related_name correcto
        platos = restaurante.platos.all()  # <-- si usaste related_name="platos"
        serializer = PlatoSerializer(platos, many=True, context={'request': request})
        return Response(serializer.data)
    

class PlatoViewSet(viewsets.ModelViewSet):
    queryset = Plato.objects.all()
    serializer_class = PlatoSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsComercio()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        rol_nombre = getattr(user.rol, "nombre", None)

        # Staff → todos los platos
        if user.is_staff:
            return Plato.objects.select_related('restaurante').all()

        # Cliente → todos los platos
        if rol_nombre == "cliente":
            return Plato.objects.select_related('restaurante').all()

        # Comercio → solo los suyos
        if rol_nombre == "comercio":
            return Plato.objects.filter(restaurante__usuario=user).select_related('restaurante')

        # Default → nada
        return Plato.objects.none()

    def get_serializer_context(self):
        return {'request': self.request}

    def perform_create(self, serializer):
        user = self.request.user
        restaurante = Restaurante.objects.filter(usuario=user).first()
        if not restaurante:
            raise PermissionDenied("No tienes un restaurante asociado.")
        
        serializer.save(restaurante=restaurante)

        registrar_auditoria(
            usuario=user,
            accion="Creación de plato",
            descripcion=f"Se creó un nuevo plato en el restaurante '{restaurante.nombre}'",
            modelo_afectado='Plato',
            objeto_id=serializer.instance.id
        )


class TipoOpcionViewSet(viewsets.ModelViewSet):
    serializer_class = TipoOpcionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.rol.nombre == 'comercio':
            # El comercio ve solo sus tipos de opciones
            return TipoOpcion.objects.filter(plato__restaurante__usuario=user)
        # Usuarios no-comercio ven todo
        return TipoOpcion.objects.all()
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.rol.nombre != 'comercio':
            raise PermissionDenied("Solo los comercios pueden crear tipos de opciones.")

        # 🔹 Obtener el plato enviado en el request
        plato_id = self.request.data.get('plato')
        plato = get_object_or_404(Plato, pk=plato_id)

        # 🔹 Asignar automáticamente el restaurante del plato
        serializer.save(restaurante=plato.restaurante)



class OpcionPlatoViewSet(viewsets.ModelViewSet):
    serializer_class = OpcionPlatoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.rol.nombre != 'comercio':
            raise PermissionDenied("Solo los comercios pueden ver opciones de plato.")
        return OpcionPlato.objects.filter(tipo__plato__restaurante__usuario=user)

    def perform_create(self, serializer):
        user = self.request.user
        if user.rol.nombre != 'comercio':
            raise PermissionDenied("Solo los comercios pueden crear opciones de plato.")

        # 🔹 Tomamos el ID del tipo desde el cuerpo del request
        tipo_id = self.request.data.get('tipo')
        if not tipo_id:
            raise PermissionDenied("Debes enviar el ID del tipo de opción.")

        # 🔹 Validamos que ese tipo pertenezca al restaurante del usuario
        tipo = get_object_or_404(TipoOpcion, id=tipo_id, plato__restaurante__usuario=user)

        # 🔹 Guardamos la opción asociándola correctamente
        serializer.save(tipo=tipo)