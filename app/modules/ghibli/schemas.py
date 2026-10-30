from pydantic import BaseModel

# Los ids de Ghibli se manejan como texto, tal como los regresa la API.
# Los campos de texto son opcionales: si Ghibli deja de mandar alguno, la API no truena.


# ---------- Versiones resumidas ----------

# Resumen de una película (usa title en lugar de name)
class FilmSummary(BaseModel):
    id: str
    title: str


# Resumen de people, locations, species y vehicles
class NamedSummary(BaseModel):
    id: str
    name: str


# ---------- Versiones completas ----------
# Los links a otros recursos se muestran como resúmenes, nunca como URLs.

class FilmDetail(BaseModel):
    id: str
    title: str
    original_title: str | None = None
    original_title_romanised: str | None = None
    image: str | None = None
    movie_banner: str | None = None
    description: str | None = None
    director: str | None = None
    producer: str | None = None
    release_date: str | None = None
    running_time: str | None = None
    rt_score: str | None = None
    people: list[NamedSummary]
    species: list[NamedSummary]
    locations: list[NamedSummary]
    vehicles: list[NamedSummary]


class PersonDetail(BaseModel):
    id: str
    name: str
    gender: str | None = None
    age: str | None = None
    eye_color: str | None = None
    hair_color: str | None = None
    films: list[FilmSummary]
    species: NamedSummary | None = None         # en Ghibli es un solo link, no una lista


class LocationDetail(BaseModel):
    id: str
    name: str
    climate: str | None = None
    terrain: str | None = None
    surface_water: str | None = None
    residents: list[NamedSummary]               # personajes que viven ahí
    films: list[FilmSummary]


class SpeciesDetail(BaseModel):
    id: str
    name: str
    classification: str | None = None
    eye_colors: str | None = None
    hair_colors: str | None = None
    people: list[NamedSummary]
    films: list[FilmSummary]


class VehicleDetail(BaseModel):
    id: str
    name: str
    description: str | None = None
    vehicle_class: str | None = None
    length: str | None = None
    pilot: NamedSummary | None = None           # personaje que lo maneja; un solo link
    films: list[FilmSummary]
