FROM itzg/minecraft-server:latest

# Set environment variables for Minecraft
ENV EULA=TRUE
ENV MEMORY=1G

# Switch to root to install packages
USER root

# Install Python, pip, and dependencies
RUN apt-get update && \
    apt-get install -y python3 python3-pip netcat-openbsd && \
    pip3 install --no-cache-dir mcrcon dotenv google-cloud-compute && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/minecraft

# Copy scripts
COPY entrypoint.sh /opt/minecraft/entrypoint.sh
COPY /vm/inactivity-check.py /opt/minecraft/inactivity-check.py
RUN chmod +x /opt/minecraft/entrypoint.sh /opt/minecraft/inactivity-check.py

# Expose Minecraft & RCON ports
EXPOSE 25565 25575

# Use custom entrypoint
ENTRYPOINT ["/opt/minecraft/entrypoint.sh"]
