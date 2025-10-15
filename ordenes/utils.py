from math import radians, cos, sin, asin, sqrt
from core.models import Conductor
from datetime import datetime
from .models import EstadoOrden
from django.utils import timezone
from datetime import timedelta
import requests

def calcular_distancia_km(lat1, lon1, lat2, lon2):
    # Fórmula de Haversine
    R = 6371  # radio de la tierra en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c


def asignar_conductor_a_orden(orden):
    restaurante = orden.restaurante

    conductores = Conductor.objects.filter(
        disponible=True,
        latitud__isnull=False,
        longitud__isnull=False
    ).exclude(
        ordenes_cliente__estado__nombre__in=["pendiente", "asignada", "Esperando aceptacion"]
    )

    candidatos = []
    for conductor in conductores:
        distancia = calcular_distancia_km(
            float(restaurante.latitud), float(restaurante.longitud),
            float(conductor.latitud), float(conductor.longitud)
        )
        if distancia <= 5:
            candidatos.append((conductor, distancia))

    if not candidatos:
        return None

    candidatos.sort(key=lambda c: c[0].ultimo_pedido or datetime.min)
    mejor_conductor = candidatos[0][0]

    # Asignamos al conductor en "Esperando aceptacion"
    orden.conductor = mejor_conductor
    try:
        estado_espera = EstadoOrden.objects.get(nombre="Esperando aceptacion")
        orden.estado = estado_espera
    except EstadoOrden.DoesNotExist:
        pass

    orden.limite_aceptacion = timezone.now() + timedelta(minutes=1)
    orden.save(update_fields=["conductor", "estado", "limite_aceptacion"])

    if mejor_conductor.push_token:
        enviar_notificacion_expo(
            conductor.push_token,
            "Nueva orden disponible",
            "Tienes 1 minuto para aceptarla",
            {"orden_id": str(orden.id)}
        )
    # Aquí disparas la notificación push/websocket
    # send_push_notification(mejor_conductor.usuario, f"Tienes una nueva orden #{orden.numero_orden}")

    return mejor_conductor

def enviar_notificacion_expo(token, titulo, mensaje, data=None):
    url = "https://exp.host/--/api/v2/push/send"
    payload = {
        "to": token,
        "title": titulo,
        "body": mensaje,
        "data": data or {},
    }
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers)
    return r.json()


def calcular_envio_usd(distancia_km):
    """Calcula el costo en USD según la distancia."""
    if distancia_km <= 1:
        return 1.00
    else:
        extra = distancia_km - 1
        return round(1.00 + (extra * 0.45), 2)


def obtener_distancia_osrm(lat_origen, lon_origen, lat_destino, lon_destino):
    """Llama a la API de ORS/OSRM y devuelve la distancia en km."""
    url = f"http://161.97.137.192:5000/route/v1/driving/{lon_origen},{lat_origen};{lon_destino},{lat_destino}?overview=false"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        distancia_metros = data["routes"][0]["distance"]
        return distancia_metros / 1000  # convertir a km
    except Exception as e:
        print("Error obteniendo distancia OSRM:", e)
        return None