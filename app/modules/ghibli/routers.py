from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.modules.auth.dependencies import require_rol
from app.modules.ghibli.cache import ghibli_cache
from app.modules.ghibli.client import GHIBLI_MAX_LIMIT, ghibli_client
from app.modules.ghibli.schemas import (
    FilmDetail,
    FilmSummary,
    LocationDetail,
    NamedSummary,
    PersonDetail,
    SpeciesDetail,
    VehicleDetail,
)
from app.modules.ghibli.service import FILMS, LOCATIONS, PEOPLE, SPECIES, VEHICLES, GhibliService
from app.modules.users.models import Rol
from app.modules.users.schemas import UserResponse

RESOURCE_NOT_FOUND = "Recurso no encontrado en Studio Ghibli"

# Los ids de Ghibli son UUID. Validarlos evita mandar a Ghibli cualquier texto en la URL.
GHIBLI_ID_PATTERN = r"^[0-9a-fA-F-]{36}$"

# Todos piden token de un usuario con rol; cada recurso además pide su rol (o admin)
router = APIRouter(prefix="/ghibli", tags=["ghibli"], dependencies=[Depends(require_rol)])


def get_ghibli_service() -> GhibliService:
    return GhibliService(ghibli_client, ghibli_cache)


# Crea una dependencia que deja pasar solo al rol del recurso o a un admin.
# Ejemplo: require_access_to(Rol.films) -> solo films y admin.
def require_access_to(resource_rol: Rol):

    def check_access(user: UserResponse = Depends(require_rol)) -> UserResponse:
        if user.rol == Rol.admin:
            return user
        if user.rol == resource_rol:
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tu rol no tiene acceso a este recurso")

    return check_access


# ---------- Films ----------

@router.get("/films", response_model=list[FilmSummary], dependencies=[Depends(require_access_to(Rol.films))])
def list_films(
    limit: int | None = Query(default=None, ge=1, le=GHIBLI_MAX_LIMIT),
    servicio_ghibli: GhibliService = Depends(get_ghibli_service),
):
    return servicio_ghibli.list_films(limit)


@router.get("/films/{film_id}", response_model=FilmDetail, dependencies=[Depends(require_access_to(Rol.films))])
def get_film(
    film_id: str = Path(pattern=GHIBLI_ID_PATTERN),
    servicio_ghibli: GhibliService = Depends(get_ghibli_service),
):
    film = servicio_ghibli.get_film(film_id)
    if film is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=RESOURCE_NOT_FOUND)
    return film


# ---------- People ----------

@router.get("/people", response_model=list[NamedSummary], dependencies=[Depends(require_access_to(Rol.people))])
def list_people(
    limit: int | None = Query(default=None, ge=1, le=GHIBLI_MAX_LIMIT),
    servicio_ghibli: GhibliService = Depends(get_ghibli_service),
):
    return servicio_ghibli.list_named(PEOPLE, limit)


@router.get("/people/{person_id}", response_model=PersonDetail, dependencies=[Depends(require_access_to(Rol.people))])
def get_person(
    person_id: str = Path(pattern=GHIBLI_ID_PATTERN),
    servicio_ghibli: GhibliService = Depends(get_ghibli_service),
):
    person = servicio_ghibli.get_person(person_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=RESOURCE_NOT_FOUND)
    return person


# ---------- Locations ----------

@router.get("/locations", response_model=list[NamedSummary], dependencies=[Depends(require_access_to(Rol.locations))])
def list_locations(
    limit: int | None = Query(default=None, ge=1, le=GHIBLI_MAX_LIMIT),
    servicio_ghibli: GhibliService = Depends(get_ghibli_service),
):
    return servicio_ghibli.list_named(LOCATIONS, limit)


@router.get("/locations/{location_id}", response_model=LocationDetail, dependencies=[Depends(require_access_to(Rol.locations))])
def get_location(
    location_id: str = Path(pattern=GHIBLI_ID_PATTERN),
    servicio_ghibli: GhibliService = Depends(get_ghibli_service),
):
    location = servicio_ghibli.get_location(location_id)
    if location is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=RESOURCE_NOT_FOUND)
    return location


# ---------- Species ----------

@router.get("/species", response_model=list[NamedSummary], dependencies=[Depends(require_access_to(Rol.species))])
def list_species(
    limit: int | None = Query(default=None, ge=1, le=GHIBLI_MAX_LIMIT),
    servicio_ghibli: GhibliService = Depends(get_ghibli_service),
):
    return servicio_ghibli.list_named(SPECIES, limit)


@router.get("/species/{species_id}", response_model=SpeciesDetail, dependencies=[Depends(require_access_to(Rol.species))])
def get_species(
    species_id: str = Path(pattern=GHIBLI_ID_PATTERN),
    servicio_ghibli: GhibliService = Depends(get_ghibli_service),
):
    species = servicio_ghibli.get_species(species_id)
    if species is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=RESOURCE_NOT_FOUND)
    return species


# ---------- Vehicles ----------

@router.get("/vehicles", response_model=list[NamedSummary], dependencies=[Depends(require_access_to(Rol.vehicles))])
def list_vehicles(
    limit: int | None = Query(default=None, ge=1, le=GHIBLI_MAX_LIMIT),
    servicio_ghibli: GhibliService = Depends(get_ghibli_service),
):
    return servicio_ghibli.list_named(VEHICLES, limit)


@router.get("/vehicles/{vehicle_id}", response_model=VehicleDetail, dependencies=[Depends(require_access_to(Rol.vehicles))])
def get_vehicle(
    vehicle_id: str = Path(pattern=GHIBLI_ID_PATTERN),
    servicio_ghibli: GhibliService = Depends(get_ghibli_service),
):
    vehicle = servicio_ghibli.get_vehicle(vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=RESOURCE_NOT_FOUND)
    return vehicle
