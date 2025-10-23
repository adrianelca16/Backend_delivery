from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import EstadoOrden, Orden
from .serializers import EstadoOrdenSerializer, OrdenSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from ubicaciones.models import UbicacionConductor
from auditoria.services import registrar_auditoria
from wallet.utils import asignar_pago_wallet_conductor
from ordenes.utils import asignar_conductor_a_orden, enviar_notificacion_expo
from django.utils import timezone
from datetime import timedelta
from ordenes.utils import obtener_distancia_osrm, calcular_envio_usd
from core.permissions import IsAdmin

class EstadoOrdenViewSet(viewsets.ModelViewSet):
    queryset = EstadoOrden.objects.all()
    serializer_class = EstadoOrdenSerializer
    permission_classes = [permissions.IsAuthenticated]



class OrdenViewSet(viewsets.ModelViewSet):
    queryset = Orden.objects.all()
    serializer_class = OrdenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.rol.nombre == 'cliente':
            return Orden.objects.filter(cliente=user)
        elif user.rol.nombre == 'conductor':
            return Orden.objects.filter(conductor__usuario=user)
        elif user.rol.nombre == 'comercio':
            return Orden.objects.filter(restaurante__usuario=user)
        return Orden.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        orden = None

        # Guardar la orden base
        if user.rol.nombre == "cliente":
            orden = serializer.save(cliente=user)
        elif user.rol.nombre == "comercio":
            orden = serializer.save(cliente=None)
        else:
            raise PermissionDenied("Solo los clientes o comercios pueden crear órdenes.")

        # 🚀 Calcular distancia y costo de envío
        try:
            lat_origen = orden.restaurante.latitud
            lon_origen = orden.restaurante.longitud
            lat_destino = orden.latitud
            lon_destino = orden.longitud

            if lat_origen and lon_origen and lat_destino and lon_destino:
                distancia_km = obtener_distancia_osrm(lat_origen, lon_origen, lat_destino, lon_destino)
                if distancia_km:
                    costo_envio = calcular_envio_usd(distancia_km)
                    orden.costo_envio = costo_envio
                    orden.save(update_fields=["costo_envio"])
        except Exception as e:
            print("Error calculando costo de envío:", e)
        
         # ✅ Notificar al comercio que hay una nueva orden
        comercio_user = orden.restaurante.usuario
        if comercio_user and comercio_user.expo_token:
            enviar_notificacion_expo(
                comercio_user.expo_token,
                "📦 Nueva orden recibida",
                f"Tienes una nueva orden del cliente {user.nombre}.",
                {"orden_id": str(orden.id)}
            )


    @action(detail=True, methods=['post'], url_path='aceptar')
    def aceptar_orden(self, request, pk=None):
        user = request.user
        try:
            conductor = user.conductor
        except:
            raise PermissionDenied("Solo los conductores pueden aceptar órdenes.")

        try:
            orden = Orden.objects.get(pk=pk, conductor=conductor)
        except Orden.DoesNotExist:
            return Response({'detail': 'Orden no disponible o no te fue asignada.'}, status=404)

        # 1️⃣ Validar expiración
        if orden.limite_aceptacion and timezone.now() > orden.limite_aceptacion:
            # Liberar conductor actual
            orden.conductor = None
            estado_pendiente = EstadoOrden.objects.get(nombre__iexact="pendiente")
            orden.estado = estado_pendiente
            orden.limite_aceptacion = None
            orden.save()

            # 2️⃣ Intentar reasignar automáticamente
            nuevo_conductor = asignar_conductor_a_orden(orden, excluir=[conductor])
            if nuevo_conductor:
                estado_espera = EstadoOrden.objects.get(nombre__iexact="Esperando aceptacion")
                orden.conductor = nuevo_conductor
                orden.estado = estado_espera
                orden.limite_aceptacion = timezone.now() + timedelta(minutes=1)
                orden.save()

                return Response({
                    'detail': f'Tiempo expirado. Orden reasignada a {nuevo_conductor.usuario.email}.'
                }, status=400)

            return Response({'detail': 'Tiempo expirado y no hay más conductores disponibles.'}, status=400)

        # 3️⃣ Si está en tiempo → aceptar correctamente
        estado_asignada = EstadoOrden.objects.get(nombre__iexact="asignada")
        orden.estado = estado_asignada
        orden.limite_aceptacion = None
        orden.save(update_fields=["estado", "limite_aceptacion"])

        cliente = orden.cliente
        if cliente and cliente.expo_token:
            enviar_notificacion_expo(
                cliente.expo_token,
                "🚗 Tu orden fue aceptada",
                f"El conductor {conductor.usuario.nombre} está en camino a recoger tu pedido.",
                {"orden_id": str(orden.id)}
            )

        return Response({'detail': 'Orden aceptada correctamente.'}, status=200)

    @action(detail=True, methods=['patch'], url_path='cambiar-estado')
    def cambiar_estado(self, request, pk=None):
        orden = self.get_object()
        user = request.user

        es_comercio = user.rol.nombre == 'comercio' and orden.restaurante.usuario == user
        es_conductor = user.rol.nombre == 'conductor' and orden.conductor.usuario == user


        if not es_comercio and not es_conductor:
            raise PermissionDenied("No tienes permiso para cambiar el estado de esta orden.")

        estado_id = request.data.get('estado')
        if not estado_id:
            return Response({'detail': 'Se requiere el ID del nuevo estado.'}, status=400)

        try:
            nuevo_estado = EstadoOrden.objects.get(pk=estado_id)
        except EstadoOrden.DoesNotExist:
            return Response({'detail': 'Estado no válido.'}, status=400)

        # --- 🚨 Flujo de asignación de conductor ---
        if nuevo_estado.nombre.lower() == 'aceptada' and not orden.conductor:
            conductor = asignar_conductor_a_orden(orden)
            if conductor:
                try:
                    estado_espera = EstadoOrden.objects.get(nombre__iexact="Esperando aceptacion")
                except EstadoOrden.DoesNotExist:
                    return Response({'detail': 'Estado "Esperando aceptacion" no existe en la BD.'}, status=500)

                orden.estado = estado_espera
                orden.save(update_fields=["conductor", "estado", "limite_aceptacion"])

                return Response({
                    'detail': f'Orden asignada al conductor {conductor.usuario.email}, esperando aceptación (1 minuto).'
                }, status=200)
            else:
                return Response({'detail': 'No hay conductores disponibles cercanos.'}, status=400)

        # --- Otros cambios de estado ---
        orden.estado = nuevo_estado
        orden.save()

        # ✅ Notificar al cliente sobre el cambio de estado
        cliente = orden.cliente
        if cliente and cliente.expo_token:
            enviar_notificacion_expo(
                cliente.expo_token,
                f"📲 Tu orden cambió de estado",
                f"La orden ahora está '{nuevo_estado.nombre}'.",
                {"orden_id": str(orden.id), "estado": nuevo_estado.nombre}
            )


        registrar_auditoria(
            usuario=request.user,
            accion="Cambio de estado",
            descripcion=f"Orden #{orden.id} cambió a '{nuevo_estado.nombre}'",
            modelo_afectado='Orden',
            objeto_id=orden.id
        )

        if nuevo_estado.nombre.lower() == 'entregada':
            asignar_pago_wallet_conductor(orden)

        return Response({'detail': f'Estado actualizado a {nuevo_estado.nombre}.'}, status=200)

    @action(detail=False, methods=['get'], url_path='disponibles')
    def disponibles(self, request):
        user = request.user
        if user.rol.nombre != 'conductor':
            raise PermissionDenied("Solo los conductores pueden ver órdenes disponibles.")

        ordenes = Orden.objects.filter(conductor__isnull=True, estado__nombre__iexact="pendiente")
        serializer = self.get_serializer(ordenes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='ubicacion-conductor')
    def ubicacion_conductor(self, request, pk=None):
        orden = self.get_object()
        if request.user != orden.cliente:
            raise PermissionDenied("No puedes ver esta ubicación.")

        if not orden.conductor:
            return Response({'detail': 'No hay conductor asignado aún.'}, status=404)

        conductor = orden.conductor
        if conductor.latitud is None or conductor.longitud is None:
            return Response({'detail': 'El conductor no tiene ubicación registrada.'}, status=404)

        return Response({
        'latitud': conductor.latitud,
        'longitud': conductor.longitud,
        'actualizado_en': conductor.ultimo_pedido  # o usa otro campo si quieres timestamp
    })
    
    @action(detail=False, methods=['get'], url_path='esperando-aceptacion')
    def esperando_aceptacion(self, request):
        user = request.user
        if user.rol.nombre.lower() != 'conductor':
            raise Response({"detail": "No eres un conductor"}, status=401)

        # Filtrar órdenes del conductor actual con estado "Esperando aceptacion"
        try:
            estado_espera = EstadoOrden.objects.get(nombre__iexact="Esperando aceptacion")
        except EstadoOrden.DoesNotExist:
            return Response({'detail': 'Estado "Esperando aceptacion" no existe.'}, status=500)

        ordenes = Orden.objects.filter(conductor__usuario=user, estado=estado_espera)
        serializer = self.get_serializer(ordenes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='mis-ordenes')
    def mis_ordenes(self, request):
        user = request.user
        try:
            conductor = user.conductor
        except:
            return Response({'detail': 'No eres un conductor'}, status=403)

        # Estados que te interesa mostrar
        estados_validos = ["asignada", "esperando aceptacion"]

        ordenes = Orden.objects.filter(
            conductor=conductor,
            estado__nombre__iexact="asignada"
        ) | Orden.objects.filter(
            conductor=conductor,
            estado__nombre__iexact="esperando aceptacion"
        )

        serializer = self.get_serializer(ordenes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='ubicaciones')
    def ubicaciones(self, request, pk=None):
        orden = self.get_object()

        cliente = orden.cliente
        direccion_cliente = getattr(cliente, "direccion", None)
        conductor = orden.conductor

        data = {
            "cliente": {
                "direccion": direccion_cliente.direccion if direccion_cliente else None,
                "latitud": direccion_cliente.latitud if direccion_cliente else None,
                "longitud": direccion_cliente.longitud if direccion_cliente else None,
            },
            "conductor": {
                "latitud": conductor.latitud if conductor else None,
                "longitud": conductor.longitud if conductor else None,
            }
        }

        return Response(data, status=200)
