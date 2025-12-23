#!/bin/bash
set -euo pipefail

# Start Minecraft server in the background
/start &

MC_PID=$!

# Wait for RCON port to be ready
echo "Waiting for Minecraft server RCON to be ready..."
while ! nc -z localhost 25575; do
    sleep 5
done

echo "Minecraft server is ready. Starting inactivity watcher..."

# Start the bash inactivity script in the background
/opt/minecraft/inactivity-script.sh &

# Note: we do NOT kill the inactivity script because it will pause the VM when idle
# The container will exit only when the Minecraft server process exits naturally

# Wait for Minecraft server to exit
wait $MC_PID
echo "Minecraft server exited. Container will stop now."
