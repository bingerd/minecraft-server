# Minecraft Server + FastAPI Controller

This project provides a **serverless-like Minecraft setup** using Docker Compose with:

- A **Minecraft server container** running the game with RCON enabled.  
- An **inactivity script** that shuts down the server if idle.  
- A **FastAPI container** to start, stop, and check the server status via a REST API.  

Everything is testable locally using Docker Compose.

---

## Architecture
```
+----------------+            +-------------------+
|  FastAPI API   |  Docker    |  Minecraft Server |
|  Container     | <------->  |  Container        |
|                |  SDK/CLI   |  + Inactivity     |
|  /start        |            |    Script         |
|  /stop         |            |  RCON Enabled     |
|  /status       |            |                   |
+----------------+            +-------------------+
```


- **FastAPI container**: Controls the Minecraft container via the Docker SDK.  
- **Minecraft container**: Runs `itzg/minecraft-server` image with `ENABLE_RCON=true`.  
- **Inactivity script**: Python script that checks for player activity via RCON every 10 seconds. If no players connect for a defined idle period, it stops the server gracefully.  

---

## Prerequisites

- Docker >= 24  
- Docker Compose  
- Python 3.11+ (for local testing the API if needed)  

---

## Running Locally

1. **Clone the repository**


2. **Build and start containers**
`docker-compose up --build`
`docker-compose up -d --build` (detached mode/no logs)

3. **Stop all containers**
`docker-compose down`

## API Endpoints
The API is exposed via FastAPI at http://localhost:8080.
| Endpoint  | Method   | Description                                     |
| --------- | -------- | ----------------------------------------------- |
| `/start`  | GET | Starts the Minecraft server container           |
| `/stop`   | GET      | Stops the Minecraft server container            |
| `/status` | GET      | Returns whether the server container is running |

### Example Usage

**Check status**
```
curl http://localhost:8080/status
# Response: {"running": true}
```

**Start the server**
```
curl -X POST http://localhost:8080/start
# Response: {"status": "started"}
```
**Stop the server**
```
curl http://localhost:8080/stop
# Response: {"status": "stopped"}
```

## Environment variables
**Minecraft container**
| Variable        | Description                             |
| --------------- | --------------------------------------- |
| `EULA`          | Must be "TRUE" to accept Minecraft EULA |
| `ENABLE_RCON`   | Enable RCON for remote commands         |
| `RCON_PASSWORD` | Password for RCON                       |
| `RCON_PORT`     | Port for RCON (default 25575)           |

**API Container**
| Variable              | Description                                                 |
| --------------------- | ----------------------------------------------------------- |
| `MINECRAFT_CONTAINER` | Container name of the Minecraft server (`minecraft-server`) |
| `MOCK`                | If `"true"`, API simulates actions without affecting Docker |

## Notes

- The inactivity script runs inside the Minecraft container at /opt/minecraft/inactivity-check.py.

- The API container uses the Docker socket (/var/run/docker.sock) to control the Minecraft container.

- The container name is explicitly set in docker-compose.yml as minecraft-server.

**This setup allows you to:**

- Run Minecraft locally in a containerized environment.

- Automatically stop the server when idle.

- Control the server via a REST API, ready for integration with external services.