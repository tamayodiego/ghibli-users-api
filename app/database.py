import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()                                   # lee el .env

SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"     # imprime el SQL solo si SQL_ECHO=true

engine = create_engine(os.environ["DATABASE_URL"], echo=SQL_ECHO)   # conexión a Postgres
SessionLocal = sessionmaker(bind=engine, autoflush=False)       # fábrica de sesiones

class Base(DeclarativeBase):                    # clase padre de los modelos
    pass

def get_db():                                   # una sesión por request
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


