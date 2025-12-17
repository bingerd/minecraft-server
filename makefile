# -----------------------------
# Config
# -----------------------------
PROJECT_ID ?= minecraft-481513
ZONE ?= europe-west1-b
VM_NAME ?= minecraft-server
SERVER_DIR ?= server
API_DIR ?= api
CLOUD_RUN_SERVICE ?= minecraft-api
REGION ?= europe-west1
MINECRAFT_PORT ?= 25565

GCLOUD := gcloud
DOCKER := docker
TERRAFORM := terraform

# -----------------------------
# Phony targets
# -----------------------------
.PHONY: all terraform vm server api stop destroy

# Deploy everything: Terraform, VM, Docker images, API
all: terraform vm server api

# -----------------------------
# Terraform: provision infrastructure
# -----------------------------
terraform:
	@echo "Initializing Terraform..."
	cd terraform && $(TERRAFORM) init
	@echo "Applying Terraform..."
	cd terraform && $(TERRAFORM) apply -auto-approve -var="project_id=$(PROJECT_ID)"

# -----------------------------
# VM: start VM and copy server files
# -----------------------------
server:
	@echo "Building Minecraft server Docker image locally..."
	$(DOCKER) build -t minecraft-server $(SERVER_DIR)

	@echo "Tagging image for Artifact Registry..."
	$(DOCKER) tag minecraft-server $(REGION)-docker.pkg.dev/$(PROJECT_ID)/minecraft-server/minecraft-server:latest

	@echo "Authenticating Docker with Artifact Registry..."
	$(GCLOUD) auth configure-docker $(REGION)-docker.pkg.dev

	@echo "Pushing Minecraft server image to Artifact Registry..."
	$(DOCKER) push $(REGION)-docker.pkg.dev/$(PROJECT_ID)/minecraft-server/minecraft-server:latest

	@echo "Creating VM with container..."
	$(GCLOUD) compute instances delete $(VM_NAME) --zone $(ZONE) --quiet || true
	$(GCLOUD) compute instances create-with-container $(VM_NAME) \
		--zone=$(ZONE) \
		--machine-type=e2-medium \
		--preemptible \
		--container-image=$(REGION)-docker.pkg.dev/$(PROJECT_ID)/minecraft-server/minecraft-server:latest \
		--container-restart-policy=always \
		--tags=minecraft-server \
		--boot-disk-size=10GB

	@echo "Creating firewall rule for Minecraft port 25565..."
	-$(GCLOUD) compute firewall-rules create allow-minecraft \
		--allow tcp:$(MINECRAFT_PORT) \
		--source-ranges 0.0.0.0/0 \
		--target-tags minecraft-server \
		--description "Allow inbound Minecraft connections"

	@echo "Minecraft server VM deployed and accessible on port $(MINECRAFT_PORT)."


# -----------------------------
# Build and push Minecraft server image
# -----------------------------
# server:
# 	@echo "Building Minecraft server Docker image locally..."
# 	$(DOCKER) build -t minecraft-server $(SERVER_DIR)

# 	@echo "Tagging image for Artifact Registry..."
# 	$(DOCKER) tag minecraft-server $(REGION)-docker.pkg.dev/$(PROJECT_ID)/minecraft-server/minecraft-server:latest

# 	@echo "Authenticating Docker with Artifact Registry..."
# 	$(GCLOUD) auth configure-docker $(REGION)-docker.pkg.dev

# 	@echo "Pushing server image to Artifact Registry..."
# 	$(DOCKER) push $(REGION)-docker.pkg.dev/$(PROJECT_ID)/minecraft-server/minecraft-server:latest

# -----------------------------
# Build and push API image, deploy to Cloud Run
# -----------------------------
api:
	@echo "Building API Docker image locally..."
	$(DOCKER) build -t minecraft-api $(API_DIR)

	@echo "Tagging image for Artifact Registry..."
	$(DOCKER) tag minecraft-api $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(CLOUD_RUN_SERVICE)/$(CLOUD_RUN_SERVICE):latest

	@echo "Authenticating Docker with Artifact Registry..."
	$(GCLOUD) auth configure-docker $(REGION)-docker.pkg.dev

	@echo "Pushing API image to Artifact Registry..."
	$(DOCKER) push $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(CLOUD_RUN_SERVICE)/$(CLOUD_RUN_SERVICE):latest

	@echo "Deploying API to Cloud Run..."
	$(GCLOUD) run deploy $(CLOUD_RUN_SERVICE) \
		--image $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(CLOUD_RUN_SERVICE)/$(CLOUD_RUN_SERVICE):latest \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated

# -----------------------------
# Stop VM to save costs
# -----------------------------
stop:
	@echo "Stopping VM..."
	$(GCLOUD) compute instances stop $(VM_NAME) --zone $(ZONE)

# -----------------------------
# Destroy Terraform-managed resources
# -----------------------------
destroy:
	@echo "Destroying Terraform-managed infrastructure..."
	cd terraform && $(TERRAFORM) destroy -auto-approve
