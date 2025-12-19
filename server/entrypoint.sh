#!/bin/bash
set -e

# Start Minecraft server in background
/start &

MC_PID=$!

# Wait for RCON port to be ready
echo "Waiting for Minecraft server RCON to be ready..."
while ! nc -z localhost 25575; do
    sleep 5
done

echo "Minecraft server is ready. Starting inactivity watcher..."

# Start the Python idle-watcher in background
/opt/venv/bin/python -u /opt/minecraft/inactivity-check.py &

PY_PID=$!

# Wait for Minecraft process to exit
wait $MC_PID
echo "Minecraft server exited. Stopping container."
