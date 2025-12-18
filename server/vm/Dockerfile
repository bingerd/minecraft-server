FROM python:3.11-slim

# Install dependencies for Python + Cloud SDK
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    gnupg \
    lsb-release \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Install Google Cloud SDK (official installer)
RUN curl -fsSL https://sdk.cloud.google.com | bash

# Add gcloud to PATH
ENV PATH=/root/google-cloud-sdk/bin:$PATH

WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir mcrcon python-dotenv

# Copy the inactivity checker script
COPY inactivity-check.py .

CMD ["python", "inactivity-check.py"]
