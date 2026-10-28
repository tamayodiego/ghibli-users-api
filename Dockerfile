FROM python:3.12-slim

# uv para instalar las dependencias desde uv.lock
COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primero solo las dependencias: esta capa se reutiliza mientras uv.lock no cambie
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

COPY app ./app

# No correr como root
RUN useradd --create-home appuser
USER appuser

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
