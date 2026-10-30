import os

# La app exige estas variables al importarse. Los tests no se conectan a la base,
# así que basta con valores de prueba (si existe un .env, no se usan).
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("JWT_SECRET_KEY", "clave-solo-para-tests-de-32-caracteres")
