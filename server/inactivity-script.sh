#!/bin/bash

# --- Config ---
MC_CONTAINER="${MC_CONTAINER:-minecraft}"   # container name
IDLE_LIMIT="${IDLE_LIMIT:-300}"             # seconds before shutdown
INTERVAL="${INTERVAL:-30}"                  # seconds between checks

VM_NAME="${VM_NAME}"                         # required
ZONE="${ZONE}"                               # required
PROJECT="${PROJECT_ID}"                       # required

last_active=$(date +%s)
echo "$(date): Last active initialized to $last_active"

# --- Function to get online players ---
get_online_players() {
    output=$(docker exec "$MC_CONTAINER" rcon-cli list 2>/dev/null)
    if [[ $output =~ There\ are\ ([0-9]+)\ of ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        echo 0
    fi
}

# --- Stop Minecraft server gracefully ---
stop_minecraft_gracefully() {
    echo "$(date): Stopping Minecraft server gracefully..."
    docker exec "$MC_CONTAINER" rcon-cli stop
    echo "$(date): Minecraft server stopped"
}

# --- Stop the VM via gcloud ---
stop_vm() {
    echo "$(date): Stopping VM via Compute Engine API..."
    gcloud compute instances stop "$VM_NAME" --zone "$ZONE" --quiet
    echo "$(date): VM stop command issued"
}

# --- Main loop ---
while true; do
    now=$(date +%s)
    players=$(get_online_players)
    echo "$(date): Players online: $players"

    if [[ "$players" -gt 0 ]]; then
        last_active=$now
    fi

    idle_time=$(( now - last_active ))
    echo "$(date): Idle time: $idle_time seconds"

    if [[ "$idle_time" -ge "$IDLE_LIMIT" ]]; then
        echo "$(date): Server idle for $idle_time seconds, shutting down..."
        stop_minecraft_gracefully
        stop_vm
        break
    fi

    sleep "$INTERVAL"
done
