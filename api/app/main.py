import os
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from googleapiclient import discovery
from google.auth import default
from google.cloud import dns_v1

app = FastAPI()

# -------------------------------
# Load environment variables
# -------------------------------
PROJECT_ID = os.getenv("PROJECT_ID", "minecraft-481513")
ZONE = os.getenv("ZONE", "europe-west1-b")
VM_NAME = os.getenv("VM_NAME", "minecraft-server")
API_TOKEN = os.getenv("API_TOKEN", "changeme")
DNS_ZONE = os.getenv("DNS_ZONE", "bngrd-com")
SUBDOMAIN = "mc.bngrd.com."

# -------------------------------
# Initialize clients
# -------------------------------
credentials, _ = default()
compute = discovery.build("compute", "v1", credentials=credentials)
dns_client = dns_v1.ManagedZonesClient()  # For listing zones
dns_changes_client = dns_v1.ChangesClient()  # For DNS record changes

# -------------------------------
# HTTP Bearer security
# -------------------------------
bearer_scheme = HTTPBearer(auto_error=False)

def check_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if not credentials or credentials.scheme.lower() != "bearer" or credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

# -------------------------------
# Redirect root to docs
# -------------------------------
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

# -------------------------------
# Helpers
# -------------------------------
def get_external_ip(instance):
    network_interfaces = instance.get("networkInterfaces", [])
    if network_interfaces:
        access_configs = network_interfaces[0].get("accessConfigs", [])
        if access_configs:
            return access_configs[0].get("natIP")
    return None

def update_dns_record(ip_address: str):
    from google.cloud import dns_v1
    from google.protobuf import field_mask_pb2

    # DNS zone path
    zone_path = f"projects/{PROJECT_ID}/managedZones/{DNS_ZONE}"

    # Get current records
    records_client = dns_v1.RecordsClient()
    existing_records = records_client.list_records(parent=zone_path)

    # Remove old A record if exists
    old_record = next((r for r in existing_records if r.name == SUBDOMAIN and r.type_ == "A"), None)
    
    changes = dns_v1.Change()
    if old_record:
        changes.deletions.append(old_record)

    # Add new A record
    new_record = dns_v1.ResourceRecordSet(
        name=SUBDOMAIN,
        type_="A",
        ttl=300,
        rrdatas=[ip_address]
    )
    changes.additions.append(new_record)

    # Apply change
    dns_changes_client.create_change(parent=zone_path, change=changes)

# -------------------------------
# Start server
# -------------------------------
@app.get("/start")
async def start_server():
    try:
        # Start the VM
        compute.instances().start(project=PROJECT_ID, zone=ZONE, instance=VM_NAME).execute()

        # Get instance info
        instance = compute.instances().get(project=PROJECT_ID, zone=ZONE, instance=VM_NAME).execute()
        external_ip = get_external_ip(instance)
        if not external_ip:
            return JSONResponse({"status": "error", "message": "No external IP found"}, status_code=500)

        # Update DNS record
        update_dns_record(external_ip)

        return JSONResponse({"status": "starting", "external_ip": external_ip}, status_code=200)

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

# -------------------------------
# Stop server (auth required)
# -------------------------------
@app.get("/stop")
async def stop_server(dep: None = Depends(check_token)):
    try:
        compute.instances().stop(project=PROJECT_ID, zone=ZONE, instance=VM_NAME).execute()
        return JSONResponse({"status": "stopping"}, status_code=200)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

# -------------------------------
# Status
# -------------------------------
@app.get("/status")
async def status():
    try:
        instance = compute.instances().get(project=PROJECT_ID, zone=ZONE, instance=VM_NAME).execute()
        running = instance.get("status") == "RUNNING"
        return JSONResponse({"running": running, "status": instance.get("status")})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

# -------------------------------
# External IP
# -------------------------------
@app.get("/ip")
async def get_external_ip():
    try:
        instance = compute.instances().get(project=PROJECT_ID, zone=ZONE, instance=VM_NAME).execute()
        ip = get_external_ip(instance)
        return JSONResponse({"external_ip": ip})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

# -------------------------------
# RCON endpoint
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
        # Optional: replace with paramiko or google-cloud-ssh if you want pure Python SSH
        import subprocess
        result = subprocess.run(ssh_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            return JSONResponse({"status": "error", "message": result.stderr.strip()}, status_code=500)

        return JSONResponse({"status": "success", "output": result.stdout.strip()})

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

# -------------------------------
# Entrypoint
# -------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
