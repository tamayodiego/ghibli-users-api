from app.modules.ghibli.cache import TimedCache
from app.modules.ghibli.client import GhibliClient
from app.modules.ghibli.schemas import (
    FilmDetail,
    FilmSummary,
    LocationDetail,
    NamedSummary,
    PersonDetail,
    SpeciesDetail,
    VehicleDetail,
)

FILMS = "films"
PEOPLE = "people"
LOCATIONS = "locations"
SPECIES = "species"
VEHICLES = "vehicles"


# Saca el id de un link de Ghibli.
#   "https://ghibliapi.vercel.app/people/598f7048-..."  -> "598f7048-..."
#   "https://ghibliapi.vercel.app/locations/"           -> None (link genérico, sin id)
def get_id_from_link(link: str) -> str | None:
    last_part = link.split("/")[-1]
    if last_part == "":
        return None
    return last_part


# Ghibli a veces manda una lista de links y a veces un solo link (texto)
def as_link_list(links: list[str] | str | None) -> list[str]:
    if links is None:
        return []
    if isinstance(links, str):
        return [links]
    return links


class GhibliService:

    def __init__(self, client: GhibliClient, cache: TimedCache):
        self.client = client
        self.cache = cache

    # ---------- Caché ----------

    # Resúmenes de un recurso, indexados por id: {"598f...": {"id": "598f...", "name": "Pazu"}}
    # Se piden a Ghibli solo la primera vez que hacen falta (o cuando expira la caché).
    def _get_summary_index(self, resource: str) -> dict[str, dict]:
        cache_key = f"summaries:{resource}"
        cached_index = self.cache.get(cache_key)
        if cached_index is not None:
            return cached_index

        if resource == FILMS:
            summary_field = "title"
        else:
            summary_field = "name"

        rows = self.client.get_list(resource, ["id", summary_field])

        summary_index = {}
        for row in rows:
            summary_index[row["id"]] = row

        self.cache.set(cache_key, summary_index)
        return summary_index

    # Un recurso completo, tal como lo regresa Ghibli. None si no existe.
    def _get_raw_detail(self, resource: str, resource_id: str) -> dict | None:
        cache_key = f"detail:{resource}:{resource_id}"
        cached_detail = self.cache.get(cache_key)
        if cached_detail is not None:
            return cached_detail

        detail = self.client.get_one(resource, resource_id)
        if detail is None:
            return None   # los 404 no se guardan en caché

        self.cache.set(cache_key, detail)
        return detail

    # ---------- Links a resúmenes ----------

    # Convierte links a resúmenes {id, name}. Ignora los links genéricos y los ids que no existen.
    def _resolve_named_links(self, links: list[str] | str | None, resource: str) -> list[NamedSummary]:
        summary_index = self._get_summary_index(resource)
        summaries = []
        for link in as_link_list(links):
            linked_id = get_id_from_link(link)
            if linked_id is None:
                continue
            if linked_id not in summary_index:
                continue
            row = summary_index[linked_id]
            summaries.append(NamedSummary(id=row["id"], name=row["name"]))
        return summaries

    # Igual que _resolve_named_links, pero para películas ({id, title})
    def _resolve_film_links(self, links: list[str] | str | None) -> list[FilmSummary]:
        summary_index = self._get_summary_index(FILMS)
        summaries = []
        for link in as_link_list(links):
            linked_id = get_id_from_link(link)
            if linked_id is None:
                continue
            if linked_id not in summary_index:
                continue
            row = summary_index[linked_id]
            summaries.append(FilmSummary(id=row["id"], title=row["title"]))
        return summaries

    # Para los campos que en Ghibli son un solo link (people.species, vehicles.pilot)
    def _resolve_single_named_link(self, link: str | None, resource: str) -> NamedSummary | None:
        summaries = self._resolve_named_links(link, resource)
        if len(summaries) == 0:
            return None
        return summaries[0]

    # ---------- Listados (versión resumida) ----------

    def _list_rows(self, resource: str, limit: int | None) -> list[dict]:
        rows = list(self._get_summary_index(resource).values())
        if limit is not None:
            rows = rows[:limit]
        return rows

    def list_films(self, limit: int | None) -> list[FilmSummary]:
        films = []
        for row in self._list_rows(FILMS, limit):
            films.append(FilmSummary(id=row["id"], title=row["title"]))
        return films

    def list_named(self, resource: str, limit: int | None) -> list[NamedSummary]:
        summaries = []
        for row in self._list_rows(resource, limit):
            summaries.append(NamedSummary(id=row["id"], name=row["name"]))
        return summaries

    # ---------- Detalles (versión completa) ----------
    # Cada uno regresa None si el recurso no existe en Ghibli.

    def get_film(self, film_id: str) -> FilmDetail | None:
        raw = self._get_raw_detail(FILMS, film_id)
        if raw is None:
            return None
        return FilmDetail(
            id=raw["id"],
            title=raw["title"],
            original_title=raw.get("original_title"),
            original_title_romanised=raw.get("original_title_romanised"),
            image=raw.get("image"),
            movie_banner=raw.get("movie_banner"),
            description=raw.get("description"),
            director=raw.get("director"),
            producer=raw.get("producer"),
            release_date=raw.get("release_date"),
            running_time=raw.get("running_time"),
            rt_score=raw.get("rt_score"),
            people=self._resolve_named_links(raw.get("people"), PEOPLE),
            species=self._resolve_named_links(raw.get("species"), SPECIES),
            locations=self._resolve_named_links(raw.get("locations"), LOCATIONS),
            vehicles=self._resolve_named_links(raw.get("vehicles"), VEHICLES),
        )

    def get_person(self, person_id: str) -> PersonDetail | None:
        raw = self._get_raw_detail(PEOPLE, person_id)
        if raw is None:
            return None
        return PersonDetail(
            id=raw["id"],
            name=raw["name"],
            gender=raw.get("gender"),
            age=raw.get("age"),
            eye_color=raw.get("eye_color"),
            hair_color=raw.get("hair_color"),
            films=self._resolve_film_links(raw.get("films")),
            species=self._resolve_single_named_link(raw.get("species"), SPECIES),
        )

    def get_location(self, location_id: str) -> LocationDetail | None:
        raw = self._get_raw_detail(LOCATIONS, location_id)
        if raw is None:
            return None
        return LocationDetail(
            id=raw["id"],
            name=raw["name"],
            climate=raw.get("climate"),
            terrain=raw.get("terrain"),
            surface_water=raw.get("surface_water"),
            residents=self._resolve_named_links(raw.get("residents"), PEOPLE),
            films=self._resolve_film_links(raw.get("films")),
        )

    def get_species(self, species_id: str) -> SpeciesDetail | None:
        raw = self._get_raw_detail(SPECIES, species_id)
        if raw is None:
            return None
        return SpeciesDetail(
            id=raw["id"],
            name=raw["name"],
            classification=raw.get("classification"),
            eye_colors=raw.get("eye_colors"),
            hair_colors=raw.get("hair_colors"),
            people=self._resolve_named_links(raw.get("people"), PEOPLE),
            films=self._resolve_film_links(raw.get("films")),
        )

    def get_vehicle(self, vehicle_id: str) -> VehicleDetail | None:
        raw = self._get_raw_detail(VEHICLES, vehicle_id)
        if raw is None:
            return None
        return VehicleDetail(
            id=raw["id"],
            name=raw["name"],
            description=raw.get("description"),
            vehicle_class=raw.get("vehicle_class"),
            length=raw.get("length"),
            pilot=self._resolve_single_named_link(raw.get("pilot"), PEOPLE),
            films=self._resolve_film_links(raw.get("films")),
        )
