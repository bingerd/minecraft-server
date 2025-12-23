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
# -------------------------------
# Start server (no auth)
# -------------------------------
@app.get("/start")
async def start_server():
    try:
        # 1. Start the VM
        compute.instances().start(
            project=PROJECT_ID,
            zone=ZONE,
            instance=VM_NAME
        ).execute()

        # 2. Get the external IP
        resp = compute.instances().get(
            project=PROJECT_ID,
            zone=ZONE,
            instance=VM_NAME
        ).execute()
        network_interfaces = resp.get("networkInterfaces", [])
        if network_interfaces:
            access_configs = network_interfaces[0].get("accessConfigs", [])
            external_ip = access_configs[0].get("natIP") if access_configs else None
        else:
            external_ip = None

        if not external_ip:
            return JSONResponse({"status": "error", "message": "No external IP found"}, status_code=500)

        # 3. Update Cloud DNS
        dns_zone = os.getenv("DNS_ZONE", "bngrd-com")  # replace with your managed zone name
        subdomain = "mc.bngrd.com."

        # Start transaction
        subprocess.run(["gcloud", "dns", "record-sets", "transaction", "start", "--zone", dns_zone], check=True)

        # Remove old A record (ignore errors if not exists)
        subprocess.run([
            "gcloud", "dns", "record-sets", "transaction", "remove",
            "--zone", dns_zone,
            "--name", subdomain,
            "--type", "A",
            "--ttl", "300",
            external_ip  # required even if old IP is different, gcloud ignores if it doesn't match
        ], check=False)

        # Add new A record
        subprocess.run([
            "gcloud", "dns", "record-sets", "transaction", "add",
            external_ip,
            "--zone", dns_zone,
            "--name", subdomain,
            "--type", "A",
            "--ttl", "300"
        ], check=True)

        # Execute transaction
        subprocess.run(["gcloud", "dns", "record-sets", "transaction", "execute", "--zone", dns_zone], check=True)

        return JSONResponse({"status": "starting", "external_ip": external_ip}, status_code=200)

    except subprocess.CalledProcessError as e:
        return JSONResponse({"status": "error", "message": f"DNS update failed: {e}"}, status_code=500)
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
