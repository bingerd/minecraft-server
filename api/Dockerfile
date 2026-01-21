FROM python:3.13-slim

WORKDIR /app

# Copy metadata AND source before install
COPY pyproject.toml .
COPY app ./app
COPY . .

# Install the project
RUN pip install --no-cache-dir .

ENV PORT=8080


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
