import os
# import docker
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

MINECRAFT_CONTAINER = os.getenv("MINECRAFT_CONTAINER", "minecraft-server")
MOCK = os.getenv("MOCK", "true").lower() == "true"

# client = docker.from_env()  # connects via /var/run/docker.sock

@app.get("/start")
async def start_server():
    if MOCK:
        return JSONResponse({"status": "mock start"}, status_code=200)
    try:
        # container = client.containers.get(MINECRAFT_CONTAINER)
        # container.start()
        return JSONResponse({"status": "started"}, status_code=200)
    # except docker.errors.NotFound:
    #     return JSONResponse({"status": "error", "message": "container not found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/stop")
async def stop_server():
    try:
        # container = client.containers.get(MINECRAFT_CONTAINER)
        # container.stop()
        return JSONResponse({"status": "stopped"}, status_code=200)
    # except docker.errors.NotFound:
    #     return JSONResponse({"status": "error", "message": "container not found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/status")
async def status():
    try:
        # container = client.containers.get(MINECRAFT_CONTAINER)
        return JSONResponse({"running": "running" == "running"})
    except Exception as e:
        return JSONResponse({"running": False})
