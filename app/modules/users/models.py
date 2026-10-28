import enum
import uuid

from sqlalchemy import Enum, text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Rol(str, enum.Enum):
    admin = "admin"
    films = "films"
    people = "people"
    locations = "locations"
    species = "species"
    vehicles = "vehicles"

class User(Base):
    __tablename__ = "users"
    # PostgreSQL genera el UUID con gen_random_uuid()
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str]
    rol: Mapped[Rol] = mapped_column(Enum(Rol, name="user_rol"))
    username: Mapped[str] = mapped_column(unique=True)          # nombre para hacer login
    password_hash: Mapped[str]                  # nunca la contraseña en texto plano
