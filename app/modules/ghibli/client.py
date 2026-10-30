import os

import httpx
from dotenv import load_dotenv

load_dotenv()                                   # lee el .env
GHIBLI_BASE_URL = os.getenv("GHIBLI_BASE_URL", "https://ghibliapi.vercel.app")
GHIBLI_TIMEOUT_SECONDS = float(os.getenv("GHIBLI_TIMEOUT_SECONDS", "5"))

# Máximo que acepta Ghibli en ?limit=. Sin limit, Ghibli regresa solo 50.
GHIBLI_MAX_LIMIT = 250


# Habla con la API de Studio Ghibli. No sabe nada de usuarios ni de roles.
#
# Errores:
#   - El recurso no existe (404)           -> regresa None
#   - Ghibli no responde a tiempo          -> lanza httpx.TimeoutException (la API responde 504)
#   - Ghibli falla o no se puede conectar  -> lanza httpx.HTTPError (la API responde 502)
class GhibliClient:

    def __init__(self, base_url: str, timeout_seconds: float):
        # Un solo cliente para toda la app: reutiliza las conexiones entre requests
        self.http = httpx.Client(base_url=base_url, timeout=timeout_seconds)

    # Listado de un recurso, solo con los campos pedidos
    def get_list(self, resource: str, fields: list[str]) -> list[dict]:
        params = {
            "fields": ",".join(fields),
            "limit": GHIBLI_MAX_LIMIT,
        }
        response = self.http.get(f"/{resource}", params=params)
        response.raise_for_status()
        return response.json()

    # Un recurso completo por id. None si no existe.
    def get_one(self, resource: str, resource_id: str) -> dict | None:
        response = self.http.get(f"/{resource}/{resource_id}")
        if response.status_code == httpx.codes.NOT_FOUND:
            return None
        response.raise_for_status()
        return response.json()


ghibli_client = GhibliClient(GHIBLI_BASE_URL, GHIBLI_TIMEOUT_SECONDS)
