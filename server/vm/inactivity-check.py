import os, time, sys
from mcrcon import MCRcon
from google.cloud import compute_v1

RCON_HOST = os.getenv("RCON_HOST", "localhost")
RCON_PORT = int(os.getenv("RCON_PORT", 25575))
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
IDLE_LIMIT = int(os.getenv("IDLE_LIMIT", 120))  # seconds
INTERVAL = int(os.getenv("INTERVAL", 10))
VM_NAME = os.getenv("VM_NAME")
ZONE = os.getenv("ZONE")
PROJECT = os.getenv("PROJECT_ID")

last_active = time.time()
compute_client = compute_v1.InstancesClient()

print("Idle monitor started", flush=True)

while True:
    now = time.time()
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            out = mcr.command("list")
            print(out, flush=True)
            if "There are 0 of a max" not in out:
                last_active = now
    except Exception as e:
        print(f"RCON not ready: {e}", flush=True)

    if now - last_active > IDLE_LIMIT:
        print("Server idle. Sending stop command...", flush=True)
        try:
            # Stop Minecraft first
            with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                mcr.command("stop")
        except Exception as e:
            print(f"RCON stop failed: {e}", flush=True)

        print("Stopping VM via API...", flush=True)
        try:
            operation = compute_client.stop(project=PROJECT, zone=ZONE, instance=VM_NAME)
            print(f"Stop operation started: {operation.name}", flush=True)
        except Exception as e:
            print(f"Failed to stop VM: {e}", flush=True)

        sys.exit(0)

    time.sleep(INTERVAL)
