FROM python:3.13-slim

WORKDIR /app

# Copy metadata AND source before install
COPY pyproject.toml .
COPY app ./app

# In your API Dockerfile
# RUN apt-get update && apt-get install -y docker.io

# Install the project
RUN pip install --no-cache-dir .

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
