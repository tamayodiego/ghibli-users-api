import os
import time
from typing import Any

from dotenv import load_dotenv

load_dotenv()                                   # lee el .env
GHIBLI_CACHE_SECONDS = int(os.getenv("GHIBLI_CACHE_SECONDS", "86400"))   # 1 día


# Caché en memoria: guarda cada valor junto con la hora en que expira.
# Vive dentro del proceso de la API; si la API se reinicia, empieza vacía.
class TimedCache:

    def __init__(self, seconds_to_live: int):
        self.seconds_to_live = seconds_to_live
        self.entries: dict[str, tuple[float, Any]] = {}

    # None si la llave no existe o ya expiró
    def get(self, key: str) -> Any | None:
        if key not in self.entries:
            return None

        expires_at, value = self.entries[key]
        if time.monotonic() > expires_at:
            del self.entries[key]
            return None

        return value

    def set(self, key: str, value: Any) -> None:
        expires_at = time.monotonic() + self.seconds_to_live
        self.entries[key] = (expires_at, value)


ghibli_cache = TimedCache(GHIBLI_CACHE_SECONDS)
