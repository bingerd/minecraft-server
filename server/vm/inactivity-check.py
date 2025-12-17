import os, sys
import time
from mcrcon import MCRcon
import dotenv

dotenv.load_dotenv()

RCON_HOST = os.getenv("RCON_HOST", "localhost")
RCON_PORT = int(os.getenv("RCON_PORT", 25575))
RCON_PASSWORD = os.getenv("RCON_PASSWORD", "changeme")
IDLE_LIMIT = int(os.getenv("IDLE_LIMIT", 3600))  # seconds
SCHEDULE_INTERVAL = int(os.getenv("SCHEDULE_INTERVAL", 60))   # seconds
STATE_FILE = "/tmp/last_active"

# If state file doesn't exist, treat container start as last activity
if not os.path.exists(STATE_FILE):
    with open(STATE_FILE, "w") as f:
        f.write(str(int(time.time())))

while True:
    now = int(time.time())

    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            players = mcr.command("list")
            if "There are 0 of a max" not in players:
                # Player online → update last activity
                with open(STATE_FILE, "w") as f:
                    f.write(str(now))
    except Exception as e:
        print(f"Error connecting to RCON: {e}", flush=True)

    # Read last active timestamp
    with open(STATE_FILE) as f:
        last = int(f.read())

    # Check idle
    if now - last > IDLE_LIMIT:
        try:
            with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                print("Server idle. Sending stop command...", flush=True)
                mcr.command("stop")
            print("Server stopped due to inactivity. Exiting container...", flush=True)
            sys.exit(0)
        except Exception as e:
            print(f"Error sending stop command: {e}", flush=True)

    time.sleep(SCHEDULE_INTERVAL)
