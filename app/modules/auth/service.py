from uuid import UUID

import jwt
from sqlalchemy.orm import Session

from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.modules.auth.security import create_access_token, decode_access_token, verify_password
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserResponse


class AuthService:

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    # None si el usuario no existe o la contraseña no coincide
    def login(self, dto: LoginRequest) -> TokenResponse | None:
        user = self.user_repo.get_by_username(dto.username)
        if user is None or not verify_password(dto.password, user.password_hash):
            return None
        return TokenResponse(access_token=create_access_token(str(user.id)))

    # None si el token es inválido, expiró o el usuario ya no existe
    def get_current_user(self, token: str) -> UserResponse | None:
        try:
            payload = decode_access_token(token)
        except jwt.InvalidTokenError:
            return None
        return self.user_repo.get_by_id(UUID(payload.sub))
