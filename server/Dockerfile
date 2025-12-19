FROM itzg/minecraft-server:latest

ENV EULA=TRUE
ENV MEMORY=1G

USER root

# Install Python and venv
RUN apt-get update && \
    apt-get install -y python3 python3-venv netcat-openbsd && \
    apt-get clean

# Create Python virtual environment
RUN python3 -m venv /opt/venv
RUN /opt/venv/bin/pip install --upgrade pip
RUN /opt/venv/bin/pip install mcstatus dotenv google-cloud-compute


WORKDIR /opt/minecraft

# Copy scripts
COPY entrypoint.sh /opt/minecraft/entrypoint.sh
COPY /vm/inactivity-check.py /opt/minecraft/inactivity-check.py
RUN chmod +x /opt/minecraft/entrypoint.sh /opt/minecraft/inactivity-check.py

# Expose Minecraft & RCON
EXPOSE 25565 25575

ENTRYPOINT ["/opt/minecraft/entrypoint.sh"]