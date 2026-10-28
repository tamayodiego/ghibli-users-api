from sqlalchemy.orm import Session

from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserResponse


class AuthService:

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def login(self, dto: LoginRequest) -> TokenResponse | None:
        pass

    def get_current_user(self, token: str) -> UserResponse | None:
        pass
