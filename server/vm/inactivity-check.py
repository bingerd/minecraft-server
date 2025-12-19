import os
import time
import subprocess
from mcstatus import JavaServer
from google.cloud import compute_v1

# --- Config ---
MC_HOST = os.getenv("MC_HOST", "127.0.0.1")
MC_PORT = int(os.getenv("MC_PORT", 25565))

IDLE_LIMIT = int(os.getenv("IDLE_LIMIT", 300))   # seconds
INTERVAL = int(os.getenv("INTERVAL", 30))

VM_NAME = os.getenv("VM_NAME")
ZONE = os.getenv("ZONE")
PROJECT = os.getenv("PROJECT_ID")

MINECRAFT_CONTAINER = os.getenv("MC_CONTAINER", "minecraft")

# --- Clients ---
compute_client = compute_v1.InstancesClient()

last_active = time.time()
print(f"Last active initialized to {last_active}", flush=True)

def get_online_players():
    try:
        server = JavaServer(MC_HOST, MC_PORT)
        status = server.status()
        return status.players.online
    except Exception as e:
        print(f"Minecraft status unavailable: {e}", flush=True)
        return None

def stop_minecraft_gracefully():
    print("Stopping Minecraft container gracefully...", flush=True)
    try:
        subprocess.run(
            ["docker", "stop", MINECRAFT_CONTAINER],
            check=True,
            timeout=120  # allow world save
        )
        print("Minecraft stopped cleanly", flush=True)
    except Exception as e:
        print(f"Failed to stop Minecraft cleanly: {e}", flush=True)

def stop_vm():
    print("Stopping VM via Compute API...", flush=True)
    try:
        operation = compute_client.stop(
            project=PROJECT,
            zone=ZONE,
            instance=VM_NAME,
        )
        print(f"VM stop operation started: {operation.name}", flush=True)
    except Exception as e:
        print(f"Failed to stop VM: {e}", flush=True)

# --- Main loop ---
while True:
    now = time.time()
    players = get_online_players()

    if players is not None:
        print(f"Players online: {players}", flush=True)
        if players > 0:
            last_active = now

    idle_time = now - last_active
    if idle_time > IDLE_LIMIT:
        print(f"Server idle for {idle_time:.0f}s", flush=True)

        stop_minecraft_gracefully()
        stop_vm()

        break

    time.sleep(INTERVAL)
