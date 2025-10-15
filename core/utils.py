import base64
import requests
from django.conf import settings

OPENROUTER_API_KEY = settings.OPENAI_API_KEY  # tu key de OpenRouter

def validar_identidad_con_gpt(foto_perfil_path, cedula_path):
    """
    Envía dos imágenes al modelo de OpenRouter para validar si
    pertenecen a la misma persona. Retorna (es_valido: bool, mensaje: str)
    """

    def encode_image(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    perfil_b64 = encode_image(foto_perfil_path)
    cedula_b64 = encode_image(cedula_path)

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://tuapp.com",  # obligatorio para OpenRouter
        "X-Title": "DeliveryExpress",          # nombre de tu app
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4.1-mini",
        "messages": [
            {
                "role": "system",
                "content": "Eres un verificador de identidad. Compara si la foto de perfil y la foto de la cédula son de la misma persona."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "¿Es la misma persona en ambas imágenes? Responde SOLO con 'SI' o 'NO' y una breve justificación."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{perfil_b64}" }},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{cedula_b64}" }}
                ]
            }
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        result = response.json()

        # 🧩 Comprobamos si vino un error explícito
        if "error" in result:
            msg = result["error"].get("message", "Error desconocido al validar identidad.")
            return False, f"❌ Error del modelo: {msg}"

        # 🧠 Comprobamos que existan 'choices'
        if "choices" not in result or not result["choices"]:
            return False, f"❌ Respuesta inesperada: {result}"

        texto = result["choices"][0]["message"]["content"].strip()

        # 🔎 Analizamos la respuesta
        if "SI" in texto.upper():
            return True, texto
        else:
            return False, texto

    except Exception as e:
        return False, f"⚠️ Error al conectar con OpenRouter: {str(e)}"
