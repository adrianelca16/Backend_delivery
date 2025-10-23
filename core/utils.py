import base64
import requests
import time
from django.conf import settings
import json


OPENROUTER_API_KEY = settings.OPENAI_API_KEY # usa la key correcta

def validar_identidad_con_gpt(foto_perfil_path, cedula_path, intentos=3):
    """
    Envía dos imágenes al modelo de OpenRouter para validar si pertenecen
    a la misma persona. Incluye reintentos automáticos ante errores intermitentes.
    Retorna (es_valido: bool, mensaje: str)
    """

    def encode_image(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    perfil_b64 = encode_image(foto_perfil_path)
    cedula_b64 = encode_image(cedula_path)

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://deliveryexpressfast.store",  # ⚠️ cambia por tu dominio en producción
        "X-Title": "DeliveryExpress",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4.1-mini",
        "messages": [
    {
        "role": "system",
        "content": (
            "Eres un experto verificador de identidad facial. "
            "Tu tarea es comparar dos fotografías y determinar si ambas pertenecen a la misma persona, "
            "centrándote únicamente en los rasgos faciales permanentes como forma del rostro, ojos, nariz, "
            "pómulos, mandíbula y proporciones generales. "
            "Ignora factores externos como cabello, barba, maquillaje, iluminación, fondo o expresión facial. "
            "Ten en cuenta que pueden haber pasado hasta 8 años entre ambas imágenes, por lo que puede haber "
            "cambios naturales en el envejecimiento."
        )
    },
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": (
                    "Compara las dos imágenes y responde en formato JSON con esta estructura:\n"
                    "{ 'mismo_rostro': true/false, 'confianza': valor entre 0 y 1, 'razon': 'breve explicación' }\n"
                    "Evalúa solo rasgos faciales. No menciones ropa, fondo ni calidad de imagen."
                )
            },
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{perfil_b64}" }},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{cedula_b64}" }}
        ]
    }
],
        "temperature": 0.2
    }

 
    for intento in range(1, intentos + 1):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=90)
            result = response.json()

            # Manejo de errores explícitos del modelo
            if "error" in result:
                msg = result["error"].get("message", "Error desconocido.")
                print(f"[⚠️ OpenRouter intento {intento}] {msg}")

                if "User not found" in msg or "timeout" in msg.lower():
                    time.sleep(2)
                    continue  # reintento automático

                return False, f"❌ Error del modelo: {msg}"

            # Verificar respuesta válida
            if "choices" not in result or not result["choices"]:
                print(f"[⚠️ OpenRouter intento {intento}] Respuesta vacía o incompleta.")
                time.sleep(2)
                continue

            texto = result["choices"][0]["message"]["content"].strip()
            print(f"[✅ Respuesta del modelo intento {intento}]: {texto}")

            # Intentar parsear JSON devuelto
            try:
                data_json = json.loads(texto.replace("'", '"'))  # por si usa comillas simples

                mismo_rostro = data_json.get("mismo_rostro", False)
                confianza = data_json.get("confianza", None)
                razon = data_json.get("razon", "")

                if mismo_rostro:
                    msg = f"✅ Coincidencia facial (confianza: {confianza if confianza else 'N/A'}). {razon}"
                    return True, msg
                else:
                    msg = f"❌ No coincide. {razon or 'Los rasgos no parecen coincidir.'}"
                    return False, msg

            except json.JSONDecodeError:
                # Si no devuelve JSON válido, usar texto plano
                if "SI" in texto.upper():
                    return True, texto
                elif "NO" in texto.upper():
                    return False, texto
                else:
                    return False, f"⚠️ Respuesta no reconocida: {texto}"

        except requests.exceptions.RequestException as e:
            print(f"[⚠️ OpenRouter intento {intento}] Error de conexión: {e}")
            time.sleep(2)

    # Si todos los intentos fallan
    return False, "⚠️ No se pudo validar identidad tras varios intentos. Intenta nuevamente."
