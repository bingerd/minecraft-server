import os
import subprocess
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from googleapiclient import discovery
from google.auth import default
import uvicorn

app = FastAPI()

# Load environment variables
PROJECT_ID = os.getenv("PROJECT_ID", "minecraft-481513")
ZONE = os.getenv("ZONE", "europe-west1-b")
VM_NAME = os.getenv("VM_NAME", "minecraft-server")
API_TOKEN = os.getenv("API_TOKEN", "changeme")  # Bearer token

# Initialize Compute Engine client
credentials, _ = default()
compute = discovery.build("compute", "v1", credentials=credentials)

# -------------------------------
# HTTP Bearer security
# -------------------------------
bearer_scheme = HTTPBearer(auto_error=False)

def check_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if not credentials or credentials.scheme.lower() != "bearer" or credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

# -------------------------------
# Redirect / to /docs
# -------------------------------
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

# -------------------------------
# Start server (no auth)
# -------------------------------
@app.get("/start")
async def start_server():
    try:
        compute.instances().start(
            project=PROJECT_ID,
            zone=ZONE,
            instance=VM_NAME
        ).execute()
        return JSONResponse({"status": "starting"}, status_code=200)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

# -------------------------------
# Stop server (auth required)
# -------------------------------
@app.get("/stop")
async def stop_server(dep: None = Depends(check_token)):
    try:
        compute.instances().stop(
            project=PROJECT_ID,
            zone=ZONE,
            instance=VM_NAME
        ).execute()
        return JSONResponse({"status": "stopping"}, status_code=200)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

# -------------------------------
# Status (no auth)
# -------------------------------
@app.get("/status")
async def status():
    try:
        resp = compute.instances().get(
            project=PROJECT_ID,
            zone=ZONE,
            instance=VM_NAME
        ).execute()
        running = resp.get("status", "") == "RUNNING"
        return JSONResponse({"running": running, "status": resp.get("status")})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

# -------------------------------
# Get external IP (no auth)
# -------------------------------
@app.get("/ip")
async def get_external_ip():
    try:
        resp = compute.instances().get(
            project=PROJECT_ID,
            zone=ZONE,
            instance=VM_NAME
        ).execute()

        network_interfaces = resp.get("networkInterfaces", [])
        if network_interfaces:
            access_configs = network_interfaces[0].get("accessConfigs", [])
            if access_configs:
                external_ip = access_configs[0].get("natIP")
                return JSONResponse({"external_ip": external_ip})
        
        return JSONResponse({"external_ip": None, "message": "No external IP found"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

# -------------------------------
# RCON endpoint (auth required)
# -------------------------------
@app.get("/rcon")
async def rcon(command: str = Query(..., description="RCON command to run"),
               dep: None = Depends(check_token)):
    try:
        ssh_command = [
            "gcloud",
            "compute",
            "ssh",
            VM_NAME,
            f"--zone={ZONE}",
            "--command",
            f"sudo docker exec minecraft rcon-cli {command}"
        ]
        result = subprocess.run(
            ssh_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            return JSONResponse({
                "status": "error",
                "message": result.stderr.strip()
            }, status_code=500)

        return JSONResponse({
            "status": "success",
            "output": result.stdout.strip()
        })

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

# -------------------------------
# Cloud Run entrypoint
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
