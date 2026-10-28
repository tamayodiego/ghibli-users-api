from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.modules.users.models import User
from app.modules.users.schemas import (
    PaginatedUsers,
    UserCreate,
    UserDeleteResponse,
    UserResponse,
)


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    # Convierte el modelo de BD al schema de respuesta
    def _to_schema(self, user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            name=user.name,
            rol=user.rol,
        )

    def get_by_id(self, user_id: UUID) -> UserResponse | None:
        user = self.db.get(User, user_id)
        return self._to_schema(user) if user else None

    def get_all(self, skip: int = 0, limit: int = 100) -> PaginatedUsers:
        total = self.db.scalar(select(func.count()).select_from(User))
        users = self.db.scalars(select(User).order_by(User.id).offset(skip).limit(limit)).all()
        return PaginatedUsers(
            total=total, skip=skip, limit=limit, data=[self._to_schema(u) for u in users]
        )

    def add(self, user: UserCreate) -> UserResponse:
        db_user = User(**user.model_dump())
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return self._to_schema(db_user)

    def update(self, user_id: UUID, data: dict) -> UserResponse | None:
        user = self.db.get(User, user_id)
        if user is None:
            return None
        for field, value in data.items():
            setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return self._to_schema(user)

    def delete(self, user_id: UUID) -> bool:
        user = self.db.get(User, user_id)
        if user is None:
            return False
        self.db.delete(user)
        self.db.commit()
        return True

    def delete_set(self, users: list[UUID]) -> UserDeleteResponse:
        found = set(self.db.scalars(select(User.id).where(User.id.in_(users))).all())
        self.db.execute(delete(User).where(User.id.in_(found)))
        self.db.commit()
        return UserDeleteResponse(
            users_deleted=[i for i in users if i in found],
            users_dont_deleted=[i for i in users if i not in found],
        )
