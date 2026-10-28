import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash

from app.modules.auth.schemas import TokenPayload


# Hashing de contraseñas y firma/lectura de JWT

load_dotenv()                                   # lee el .env
SECRET_KEY = os.environ["JWT_SECRET_KEY"]       # firma de los tokens
EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()      # argon2


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


# subject: el id del usuario, se guarda en "sub"
def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
    return jwt.encode({"sub": subject, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


# Lanza jwt.InvalidTokenError si el token es inválido o ya expiró
def decode_access_token(token: str) -> TokenPayload:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return TokenPayload(**payload)
