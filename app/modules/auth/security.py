from app.modules.auth.schemas import TokenPayload


# Hashing de contraseñas y firma/lectura de JWT


def hash_password(password: str) -> str:
    pass


def verify_password(password: str, hashed_password: str) -> bool:
    pass


def create_access_token(subject: str) -> str:
    pass


def decode_access_token(token: str) -> TokenPayload:
    pass
