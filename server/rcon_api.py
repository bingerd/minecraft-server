# /opt/minecraft/rcon_api.py
from fastapi import FastAPI, Header, HTTPException
import subprocess
import os

app = FastAPI()

API_KEY = os.environ.get("RCON_API_KEY")

if not API_KEY:
    raise RuntimeError("RCON_API_KEY environment variable not set")

@app.post("/rcon")
def run_rcon(
    command: str,
    x_api_key: str = Header(None)
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = subprocess.run(
        ["rcon-cli", command],
        capture_output=True,
        text=True
    )

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }
