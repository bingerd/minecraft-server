FROM itzg/minecraft-server:latest

ENV EULA=true
USER root

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-venv \ 
    netcat-openbsd \
    curl \
    apt-transport-https \
    gnupg \
    lsb-release \
    ca-certificates \
    libffi-dev \
    libssl-dev

# Add Google Cloud SDK repo key
RUN curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" \
    | tee /etc/apt/sources.list.d/google-cloud-sdk.list && \
    apt-get update && apt-get install -y google-cloud-sdk

# Create Python virtual environment
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install mcstatus google-cloud-compute fastapi uvicorn


WORKDIR /opt/minecraft

# Copy scripts
COPY inactivity-script.sh /opt/minecraft/inactivity-script.sh
COPY entrypoint.sh /opt/minecraft/entrypoint.sh
COPY rcon_api.py /opt/minecraft/rcon_api.py
# RUN dos2unix /opt/minecraft/entrypoint.sh /opt/minecraft/inactivity-script.sh
RUN chmod +x /opt/minecraft/entrypoint.sh /opt/minecraft/inactivity-script.sh

# Add Cloud SDK to PATH
ENV PATH=$PATH:/usr/bin/google-cloud-sdk/bin

# Expose Minecraft & RCON
EXPOSE 8000 25565 25575

ENTRYPOINT ["/opt/minecraft/entrypoint.sh"]