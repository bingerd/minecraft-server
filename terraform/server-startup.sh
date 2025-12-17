#!/bin/bash
# Install Docker & Docker Compose
apt-get update
apt-get install -y docker.io docker-compose git

# Optional: Clone your repo if not copying manually
cd /home
if [ ! -d "server" ]; then
    git clone https://github.com/<YOUR-USERNAME>/<YOUR-REPO>.git
fi

cd server

# Run Docker Compose
docker-compose down || true
docker-compose up -d
