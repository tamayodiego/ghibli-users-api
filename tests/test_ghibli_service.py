import unittest
from unittest.mock import patch

from app.modules.ghibli.cache import TimedCache
from app.modules.ghibli.service import GhibliService

BASE = "https://ghibliapi.vercel.app"

FILM = {
    "id": "film-1",
    "title": "Castle in the Sky",
    "people": [f"{BASE}/people/person-1"],
    "species": [f"{BASE}/species/"],          # link genérico, sin id
    "locations": [],
    "vehicles": [],
}


# Sustituye al GhibliClient: responde con datos fijos y cuenta las llamadas
class FakeClient:

    def __init__(self):
        self.calls = 0

    def get_list(self, resource, fields):
        self.calls += 1
        if resource == "people":
            return [{"id": "person-1", "name": "Pazu"}]
        return []

    def get_one(self, resource, resource_id):
        self.calls += 1
        if resource == "films" and resource_id == "film-1":
            return FILM
        return None


class GhibliServiceTests(unittest.TestCase):

    def setUp(self):
        self.client = FakeClient()
        self.service = GhibliService(self.client, TimedCache(60))

    def test_film_links_become_summaries(self):
        film = self.service.get_film("film-1")

        self.assertEqual([p.name for p in film.people], ["Pazu"])
        self.assertEqual(film.species, [])   # el link genérico se ignora

    def test_second_request_uses_the_cache(self):
        self.service.get_film("film-1")
        calls_after_first = self.client.calls
        self.service.get_film("film-1")

        self.assertEqual(self.client.calls, calls_after_first)

    def test_missing_resource_returns_none_and_is_not_cached(self):
        self.assertIsNone(self.service.get_film("no-existe"))
        self.service.get_film("no-existe")

        self.assertEqual(self.client.calls, 2)


class TimedCacheTests(unittest.TestCase):

    def test_entries_expire(self):
        cache = TimedCache(60)

        with patch("app.modules.ghibli.cache.time.monotonic", return_value=1000.0):
            cache.set("llave", "valor")
            self.assertEqual(cache.get("llave"), "valor")

        with patch("app.modules.ghibli.cache.time.monotonic", return_value=1061.0):
            self.assertIsNone(cache.get("llave"))
