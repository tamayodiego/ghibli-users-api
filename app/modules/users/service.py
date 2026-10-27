from sqlalchemy.orm import Session

from app.modules.users.repository import UserRepository
from app.modules.users.schemas import (
    PaginatedUsers,
    UserCreate,
    UserDelete,
    UserDeleteResponse,
    UserPatch,
    UserResponse,
    UserUpdate,
)


class UserService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    def create_user(self, dto: UserCreate) -> UserResponse:
        return self.repo.add(dto)

    def seek_user_by_id(self, id: int) -> UserResponse | None:
        return self.repo.get_by_id(id)

    def get_all(self, skip: int, limit: int) -> PaginatedUsers:
        return self.repo.get_all(skip, limit)

    def update(self, id: int, dto: UserUpdate | UserPatch) -> UserResponse | None:
        # exclude_unset: en PATCH solo se actualizan los campos que vienen en el body
        return self.repo.update(id, dto.model_dump(exclude_unset=True))

    def delete(self, id: int) -> bool:
        return self.repo.delete(id)

    def delete_many(self, dto: UserDelete) -> UserDeleteResponse:
        return self.repo.delete_set(dto.users)
