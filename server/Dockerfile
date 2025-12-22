FROM itzg/minecraft-server:latest

ENV EULA=TRUE
ENV MEMORY=1G

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
RUN curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg

# Add Cloud SDK repository
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" \
    | tee /etc/apt/sources.list.d/google-cloud-sdk.list

# Install Google Cloud SDK
RUN apt-get update && apt-get install -y google-cloud-sdk

# Create Python virtual environment
RUN python3 -m venv /opt/venv
RUN /opt/venv/bin/pip install --upgrade pip
RUN /opt/venv/bin/pip install mcstatus dotenv google-cloud-compute


WORKDIR /opt/minecraft

# Copy scripts
COPY entrypoint.sh /opt/minecraft/entrypoint.sh
COPY /vm/inactivity-check.py /opt/minecraft/inactivity-check.py
RUN chmod +x /opt/minecraft/entrypoint.sh /opt/minecraft/inactivity-check.py

# Add Cloud SDK to PATH
ENV PATH=$PATH:/usr/bin/google-cloud-sdk/bin


# Expose Minecraft & RCON
EXPOSE 25565 25575

ENTRYPOINT ["/opt/minecraft/entrypoint.sh"]