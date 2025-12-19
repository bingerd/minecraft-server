FROM python:3.13-slim

# Install dependencies for Python + Cloud SDK
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    gnupg \
    lsb-release \
    sudo \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir mcrcon python-dotenv google-cloud-compute

# Copy the inactivity checker script
COPY inactivity-check.py .

CMD ["python", "-u", "inactivity-check.py"]
