import os
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from googleapiclient import discovery
from google.auth import default
import paramiko  # for SSH RCON
import time
import requests

app = FastAPI()

# -------------------------------
# Load environment variables
# -------------------------------
PROJECT_ID = os.getenv("PROJECT_ID", "minecraft-481513")
ZONE = os.getenv("ZONE", "europe-west1-b")
VM_NAME = os.getenv("VM_NAME", "minecraft-server")
API_TOKEN = os.getenv("API_TOKEN", "changeme")
SSH_USER = os.getenv("SSH_USER", "your-ssh-user")
SSH_KEY_PATH = os.getenv("SSH_KEY_PATH", "~/.ssh/id_rsa")  # path to your private key

# Cloudflare config
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "Pw3CRMswloniTqzmXvZrqHxIm-vAr9JYV5YWxspc")
CLOUDFLARE_ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID", "0479794b26e6322d9ebf93efb5584d1c")  # get from dashboard
SUBDOMAIN = "mc.bngrd.com"

# curl "https://api.cloudflare.com/client/v4/user/tokens/verify" \
# -H "Authorization: Bearer Pw3CRMswloniTqzmXvZrqHxIm-vAr9JYV5YWxspc"

# -------------------------------
# Initialize clients
# -------------------------------
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

def update_cloudflare_dns(ip_address: str):
    """Update Cloudflare A record via API."""
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    # Get existing DNS records
    url = f"https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ZONE_ID}/dns_records"
    resp = requests.get(url, headers=headers).json()
    record = next((r for r in resp["result"] if r["name"] == SUBDOMAIN), None)

    data = {
        "type": "A",
        "name": SUBDOMAIN,
        "content": ip_address,
        "ttl": 60,
        "proxied": False  # Important for Minecraft
    }

    if record:
        requests.put(f"{url}/{record['id']}", headers=headers, json=data)
    else:
        requests.post(url, headers=headers, json=data)

def run_ssh_command(host, command):
    """Run SSH command using Paramiko."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username=SSH_USER, key_filename=os.path.expanduser(SSH_KEY_PATH))
    stdin, stdout, stderr = ssh.exec_command(command)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    ssh.close()
    if err:
        raise Exception(err)
    return out

# -------------------------------
# Start server
# -------------------------------
@app.get("/start")
async def start_server():
    try:
        # Start the VM
        compute.instances().start(project=PROJECT_ID, zone=ZONE, instance=VM_NAME).execute()

        # Wait until VM is RUNNING
        for _ in range(30):
            instance = compute.instances().get(project=PROJECT_ID, zone=ZONE, instance=VM_NAME).execute()
            if instance.get("status") == "RUNNING":
                break
            time.sleep(2)
        else:
            return JSONResponse({"status": "error", "message": "VM did not start in time"}, status_code=500)

        external_ip = get_external_ip(instance)
        if not external_ip:
            return JSONResponse({"status": "error", "message": "No external IP found"}, status_code=500)

        # Update Cloudflare DNS record
        update_cloudflare_dns(external_ip)

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
async def get_ip():
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
        instance = compute.instances().get(project=PROJECT_ID, zone=ZONE, instance=VM_NAME).execute()
        host_ip = get_external_ip(instance)
        if not host_ip:
            return JSONResponse({"status": "error", "message": "No external IP found"}, status_code=500)

        output = run_ssh_command(host_ip, f"sudo docker exec minecraft rcon-cli {command}")
        return JSONResponse({"status": "success", "output": output})

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

# -------------------------------
# Entrypoint
# -------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
