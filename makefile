# ======================
# Configuration
# ======================
PROJECT_ID := minecraft-481513
REGION     := europe-west1
ZONE       := europe-west1-b

VM_NAME := minecraft-server
CLOUD_RUN_SERVICE := minecraft-api

GCLOUD    := gcloud
DOCKER    := docker
TERRAFORM := terraform

SERVER_DIR  := server
SIDECAR_DIR := server/vm
API_DIR     := api

SERVER_IMAGE  := $(REGION)-docker.pkg.dev/$(PROJECT_ID)/minecraft-server/minecraft-server:latest
SIDECAR_IMAGE := $(REGION)-docker.pkg.dev/$(PROJECT_ID)/minecraft-server/inactivity-sidecar:latest
API_IMAGE     := $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(CLOUD_RUN_SERVICE)/$(CLOUD_RUN_SERVICE):latest

# ======================
# Phony targets
# ======================
.PHONY: all auth server sidecar api push update deploy cloudrun stop destroy clean

all: deploy

# ----------------------
# Auth
# ----------------------
auth:
	@echo "Authenticating Docker with Artifact Registry..."
	$(GCLOUD) auth configure-docker $(REGION)-docker.pkg.dev

# ----------------------
# Build images
# ----------------------
server:
	@echo "Building Minecraft server image..."
	$(DOCKER) build -t minecraft-server $(SERVER_DIR)
	$(DOCKER) tag minecraft-server $(SERVER_IMAGE)

sidecar:
	@echo "Building inactivity sidecar image..."
	$(DOCKER) build -t inactivity-sidecar $(SIDECAR_DIR)
	$(DOCKER) tag inactivity-sidecar $(SIDECAR_IMAGE)

api:
	@echo "Building API image..."
	$(DOCKER) build -t minecraft-api $(API_DIR)
	$(DOCKER) tag minecraft-api $(API_IMAGE)

# ----------------------
# Push images
# ----------------------
push: auth
	@echo "Pushing Minecraft server image..."
	$(DOCKER) push $(SERVER_IMAGE)

	@echo "Pushing inactivity sidecar image..."
	$(DOCKER) push $(SIDECAR_IMAGE)

	@echo "Pushing API image..."
	$(DOCKER) push $(API_IMAGE)

# ----------------------
# Update running VM
# ----------------------
update:
	@echo "Updating Minecraft server container..."
	$(GCLOUD) compute instances update-container $(VM_NAME) \
		--zone=$(ZONE) \
		--container-image=$(SERVER_IMAGE)

# ----------------------
# Full deploy (VM only)
# ----------------------
deploy: server sidecar api push update
	@echo "✅ Minecraft server & sidecar deployed. Cloud Run deploy not executed."

# ----------------------
# Deploy Cloud Run API
# ----------------------
cloudrun: api push
	@echo "Deploying API to Cloud Run..."
	$(GCLOUD) run deploy $(CLOUD_RUN_SERVICE) \
		--image $(API_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated
	@echo "✅ Cloud Run deployment complete"

# ----------------------
# Stop VM to save costs
# ----------------------
stop:
	@echo "Stopping VM..."
	$(GCLOUD) compute instances stop $(VM_NAME) --zone $(ZONE)

# ----------------------
# Destroy Terraform-managed resources
# ----------------------
destroy:
	@echo "Destroying Terraform-managed infrastructure..."
	cd terraform && $(TERRAFORM) destroy -auto-approve

# ----------------------
# Cleanup local images
# ----------------------
clean:
	@echo "Cleaning up local Docker images..."
	-$(DOCKER) rmi minecraft-server inactivity-sidecar minecraft-api || true
