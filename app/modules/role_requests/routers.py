from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.role_requests.models import RoleRequestStatus
from app.modules.role_requests.schemas import (
    PaginatedRoleRequests,
    RoleRequestCreate,
    RoleRequestResponse,
    RoleRequestReview,
)
from app.modules.role_requests.service import RoleRequestService
from app.modules.users.schemas import UserResponse

REQUEST_NOT_FOUND = "Solicitud no encontrada"
ALREADY_HAS_ROL = "Ya tienes ese rol"
ALREADY_HAS_PENDING_REQUEST = "Ya tienes una solicitud pendiente"
NO_REQUESTS = "No tienes solicitudes"
ALREADY_REVIEWED = "La solicitud ya fue revisada"

# Todos piden token. Un usuario sin rol también puede solicitar uno.
router = APIRouter(prefix="/role-requests", tags=["role-requests"], dependencies=[Depends(get_current_user)])


def get_role_request_service(db: Session = Depends(get_db)) -> RoleRequestService:
    return RoleRequestService(db)


# ---------- Usuario autenticado ----------

# Crear una solicitud de rol
@router.post("/", response_model=RoleRequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(
    request_dto: RoleRequestCreate,
    user: UserResponse = Depends(get_current_user),
    servicio_solicitudes: RoleRequestService = Depends(get_role_request_service),
):
    if servicio_solicitudes.already_has_rol(user, request_dto):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=ALREADY_HAS_ROL)

    role_request = servicio_solicitudes.create(user, request_dto)
    if role_request is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=ALREADY_HAS_PENDING_REQUEST)

    return role_request


# Mis solicitudes
@router.get("/me", response_model=list[RoleRequestResponse])
def get_my_requests(
    user: UserResponse = Depends(get_current_user),
    servicio_solicitudes: RoleRequestService = Depends(get_role_request_service),
):
    return servicio_solicitudes.get_my_requests(user)


# Mi última solicitud
@router.get("/me/last", response_model=RoleRequestResponse)
def get_my_last_request(
    user: UserResponse = Depends(get_current_user),
    servicio_solicitudes: RoleRequestService = Depends(get_role_request_service),
):
    role_request = servicio_solicitudes.get_my_last_request(user)
    if role_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NO_REQUESTS)
    return role_request


# ---------- Solo admin ----------

# Listar solicitudes, con filtro opcional por estado
@router.get("/", response_model=PaginatedRoleRequests, dependencies=[Depends(require_admin)])
def list_requests(
    status_filter: RoleRequestStatus | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    servicio_solicitudes: RoleRequestService = Depends(get_role_request_service),
):
    return servicio_solicitudes.get_all(status_filter, skip, limit)


# Obtener una solicitud por folio (6 dígitos)
@router.get("/folio/{folio}", response_model=RoleRequestResponse, dependencies=[Depends(require_admin)])
def get_request_by_folio(
    folio: str = Path(pattern=r"^\d{6}$"),
    servicio_solicitudes: RoleRequestService = Depends(get_role_request_service),
):
    role_request = servicio_solicitudes.get_by_folio(folio)
    if role_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=REQUEST_NOT_FOUND)
    return role_request


# Obtener una solicitud por id
@router.get("/{request_id}", response_model=RoleRequestResponse, dependencies=[Depends(require_admin)])
def get_request_by_id(
    request_id: UUID,
    servicio_solicitudes: RoleRequestService = Depends(get_role_request_service),
):
    role_request = servicio_solicitudes.get_by_id(request_id)
    if role_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=REQUEST_NOT_FOUND)
    return role_request


# Aprobar una solicitud: el usuario recibe el rol solicitado
@router.post("/{request_id}/approve", response_model=RoleRequestResponse)
def approve_request(
    request_id: UUID,
    review_dto: RoleRequestReview | None = None,
    admin: UserResponse = Depends(require_admin),
    servicio_solicitudes: RoleRequestService = Depends(get_role_request_service),
):
    if review_dto is None:
        review_dto = RoleRequestReview()

    if servicio_solicitudes.get_by_id(request_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=REQUEST_NOT_FOUND)

    role_request = servicio_solicitudes.approve(request_id, admin, review_dto)
    if role_request is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=ALREADY_REVIEWED)

    return role_request


# Negar una solicitud
@router.post("/{request_id}/reject", response_model=RoleRequestResponse)
def reject_request(
    request_id: UUID,
    review_dto: RoleRequestReview | None = None,
    admin: UserResponse = Depends(require_admin),
    servicio_solicitudes: RoleRequestService = Depends(get_role_request_service),
):
    if review_dto is None:
        review_dto = RoleRequestReview()

    if servicio_solicitudes.get_by_id(request_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=REQUEST_NOT_FOUND)

    role_request = servicio_solicitudes.reject(request_id, admin, review_dto)
    if role_request is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=ALREADY_REVIEWED)

    return role_request
