import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from googleapiclient import discovery
from google.auth import default
import uvicorn

app = FastAPI()

# Load environment variables
PROJECT_ID = os.getenv("PROJECT_ID", "minecraft-481513")
ZONE = os.getenv("ZONE", "europe-west1-b")
VM_NAME = os.getenv("VM_NAME", "minecraft-server")

# Initialize Compute Engine client
credentials, _ = default()
compute = discovery.build("compute", "v1", credentials=credentials)


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


@app.get("/stop")
async def stop_server():
    try:
        compute.instances().stop(
            project=PROJECT_ID,
            zone=ZONE,
            instance=VM_NAME
        ).execute()
        return JSONResponse({"status": "stopping"}, status_code=200)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


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


@app.get("/ip")
async def get_external_ip():
    try:
        resp = compute.instances().get(
            project=PROJECT_ID,
            zone=ZONE,
            instance=VM_NAME
        ).execute()

        # Extract external IP
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
# Cloud Run entrypoint
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)