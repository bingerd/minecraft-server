#!/bin/bash
set -e

# Start Minecraft server as PID 1
/start &
echo "Waiting for Minecraft server RCON to be ready..."

# Wait until RCON port is ready
while ! nc -z localhost 25575; do
    sleep 5
done

echo "Minecraft server is ready. Starting inactivity script..."

# Run Python inactivity script in a loop
/opt/venv/bin/python -u /opt/minecraft/inactivity-check.py

/start