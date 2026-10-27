from sqlalchemy.orm import Session

from app.modules.users.schemas import (
    PaginatedUsers,
    UserCreate,
    UserDeleteResponse,
    UserResponse,
)


# Datos dummy hasta implementar la persistencia con el ORM
class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> UserResponse | None:
        return UserResponse(id=user_id, name="Totoro", rol="user")

    def get_all(self, skip: int = 0, limit: int = 100) -> PaginatedUsers:
        users = [
            UserResponse(id=1, name="Totoro", rol="admin"),
            UserResponse(id=2, name="Chihiro", rol="user"),
        ]
        return PaginatedUsers(total=len(users), skip=skip, limit=limit, data=users)

    def add(self, user: UserCreate) -> UserResponse:
        return UserResponse(id=1, **user.model_dump())

    def update(self, user_id: int, data: dict) -> UserResponse | None:
        user = self.get_by_id(user_id)
        if user is None:
            return None
        return user.model_copy(update=data)

    def delete(self, user_id: int) -> bool:
        return True

    def delete_set(self, users: list[int]) -> UserDeleteResponse:
        return UserDeleteResponse(users_deleted=users, users_dont_deleted=[])
