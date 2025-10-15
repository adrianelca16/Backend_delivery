import hmac, hashlib, time, requests
from django.conf import settings
from ordenes.models import EstadoOrden

def verificacion_pago(pago):
    """
    Verifica en el banco si el pago móvil existe.
    Actualiza el campo confirmado y la orden si aplica.
    """

    # 🔹 Datos fijos para pruebas
    cliente = "J000000502665986"
    telefono = "00584123255030"       # Número fijo
    fecha_inicio = "20250801"         # Fecha fija de inicio
    fecha_fin = "20250927"            # Fecha fija de fin
    referencia = "000000573031"      # Se usa la referencia del pago registrado

    api_key = "69aeaffd289840ec9b034c45b04ab5ca"
    api_secret = "c4c9ed9d2f3b41d1ba665e02eaa48d98"
    api_path = "v1/pagos/p2p"
    nonce = str(int(time.time() * 1000))
    signature_string = f"/{api_path}{nonce}"

    signature = hmac.new(
        api_secret.encode(),
        signature_string.encode(),
        hashlib.sha384
    ).hexdigest()

    url = f"https://apiqa.bancoplaza.com:8585/{api_path}/{cliente}?canal=23&fi={fecha_inicio}&ff={fecha_fin}&tlf={telefono}"

    headers = {
        "api-key": api_key,
        "api-signature": signature,
        "nonce": nonce,
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        print(data) 

        pagos = data.get("pagos", [])
        encontrado = any(p["referencia"] == referencia for p in pagos)

        print(encontrado)

        if encontrado:
            # Confirmar el pago
            pago.confirmado = True
            pago.save(update_fields=["confirmado"])

            # Cambiar orden a pendiente
            # Cambiar orden a pendiente
            estado_pendiente = EstadoOrden.objects.get(nombre__iexact="Pendiente")
            pago.orden.estado = estado_pendiente
            pago.orden.save(update_fields=["estado"])  # ✅ guardar la orden, no el estado


        return encontrado

    except requests.RequestException as e:
        print("Error consultando banco:", str(e))
        return False
