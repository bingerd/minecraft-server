TODO:
1. startup-script: Error response from daemon: error from registry: Unauthenticated request. Unauthenticated requests do not have permission "artifactregistry.repositories.downloadArtifacts" on resource "projects/minecraft-481513/locations/europe-west1/repositories/minecraft-server" (or it may not exist)

2. Fix API 


  metadata_startup_script = <<-EOF
#!/bin/bash
set -eux

# Install Docker & Python
apt-get update
apt-get install -y python3 python3-venv netcat-openbsd curl
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# Pull Minecraft server image
docker pull ${var.minecraft_image}

# Create directories
mkdir -p /opt/minecraft/data

# Copy inactivity script
cat <<'SCRIPT' >/opt/minecraft/inactivity-check.py
#!/usr/bin/env python3
${file("${path.module}/../server/vm/inactivity-check.py")}
SCRIPT
chmod +x /opt/minecraft/inactivity-check.py

# Create systemd service for Minecraft server
cat <<SERVICE >/etc/systemd/system/minecraft.service
[Unit]
Description=Minecraft Server
After=docker.service
Requires=docker.service

[Service]
Restart=always
ExecStart=/usr/bin/docker run --name minecraft-server -p 25565:25565 -v /opt/minecraft/data:/data -e EULA=TRUE -e MEMORY=2G ${var.minecraft_image}
ExecStop=/usr/bin/docker stop minecraft-server
TimeoutStopSec=120

[Install]
WantedBy=multi-user.target
SERVICE

# Create systemd service for inactivity checker
cat <<SERVICE >/etc/systemd/system/minecraft-inactivity.service
[Unit]
Description=Minecraft Inactivity Watcher
After=minecraft.service
Requires=minecraft.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/minecraft/inactivity-check.py
Restart=no

[Install]
WantedBy=multi-user.target
SERVICE

# Enable and start services
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable minecraft
systemctl start minecraft
systemctl enable minecraft-inactivity
systemctl start minecraft-inactivity
EOF

  service_account {
    email  = google_service_account.minecraft_vm.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    }
