FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy metadata AND source before install
COPY pyproject.toml .
COPY app ./app
COPY static ./static
COPY templates ./templates

# Install the project
# RUN pip install --no-cache-dir .
RUN uv sync

EXPOSE 8080


CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
