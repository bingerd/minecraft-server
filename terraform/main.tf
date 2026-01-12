provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

###########################
# Firewall for Minecraft
###########################
resource "google_compute_firewall" "minecraft" {
  name    = "allow-minecraft"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["25565"]
  }

  allow {
    protocol = "tcp"
    ports = ["25575", "8000"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["minecraft-server"]
}

###########################
# Service Account for VM
###########################
resource "google_service_account" "minecraft_vm" {
  account_id   = "minecraft-vm-sa"
  display_name = "Minecraft VM Service Account"
}

###########################
# IAM Roles for VM SA
###########################
resource "google_project_iam_member" "vm_self_delete" {
  project = var.project_id
  role    = "roles/compute.instanceAdmin.v1"
  member  = "serviceAccount:${google_service_account.minecraft_vm.email}"
}

resource "google_project_iam_member" "vm_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.minecraft_vm.email}"
}

resource "google_project_iam_member" "minecraft_artifact_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.minecraft_vm.email}"
}

###########################
# GCS Bucket for Backups
###########################
resource "google_storage_bucket" "minecraft_backups" {
  name                        = "${var.project_id}-minecraft-backups"
  location                    = var.region
  uniform_bucket_level_access = true
}

resource "google_storage_bucket_iam_member" "minecraft_vm_write" {
  bucket = google_storage_bucket.minecraft_backups.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.minecraft_vm.email}"
}

###########################
# Persistent Disk (World)
###########################
resource "google_compute_disk" "minecraft_data" {
  name = "minecraft-data"
  zone = var.zone
  type = "pd-balanced"
  size = 20

  lifecycle {
    prevent_destroy = false
  }
}

###########################
# Minecraft VM (Ubuntu + Docker)
###########################
resource "google_compute_instance" "minecraft" {
  name         = var.vm_name
  machine_type = "e2-medium"
  zone         = var.zone
  tags         = ["minecraft-server"]

  service_account {
    email  = google_service_account.minecraft_vm.email
    scopes = ["cloud-platform"]
  }

  scheduling {
    preemptible       = true
    automatic_restart = false
  }

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 10
    }
  }

  attached_disk {
    source      = google_compute_disk.minecraft_data.id
    device_name = "minecraft-data"
  }

  network_interface {
    network       = "default"
    access_config {}
  }

  ###########################
  # Startup Script (SAFE)
  ###########################
  metadata_startup_script = <<-EOF
#!/bin/bash
set -e

apt-get update
apt-get install -y docker.io
systemctl enable docker
systemctl start docker

DISK=/dev/disk/by-id/google-minecraft-data
MOUNT=/mnt/disks/minecraft-data

mkdir -p "$MOUNT"

if ! blkid "$DISK" >/dev/null 2>&1; then
  mkfs.ext4 -F "$DISK"
fi

if ! mountpoint -q "$MOUNT"; then
  mount "$DISK" "$MOUNT"
fi

grep -q "$MOUNT" /etc/fstab || echo "$DISK $MOUNT ext4 defaults,nofail 0 2" >> /etc/fstab

docker rm -f minecraft || true

gcloud auth configure-docker europe-west1-docker.pkg.dev --quiet

docker run -d \
  --name minecraft \
  --restart unless-stopped \
  -p 25565:25565 \
  -p 25575:25575 \
  -p 8000:8000 \
  -e EULA=TRUE \
  -e MEMORY=2G \
  -e ENABLE_RCON=true \
  -e RCON_PORT=25575 \
  -e RCON_PASSWORD=${var.rcon_api_key} \
  -e VM_NAME=${var.vm_name} \
  -e ZONE=${var.zone} \
  -e PROJECT_ID=${var.project_id} \
  -e RCON_API_KEY=${var.rcon_api_key} \
  -v "$MOUNT:/data" \
  ${var.minecraft_image}
EOF
}

###########################
# Cloud Run API
###########################
resource "google_cloud_run_service" "api" {
  name     = "minecraft-api"
  location = var.region

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"  = "1"
        "run.googleapis.com/cpu-throttling" = "false"
      }
    }

    spec {
      containers {
        image = var.api_image

        ports {
          container_port = 8080
        }

        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "ZONE"
          value = var.zone
        }

        env {
          name  = "VM_NAME"
          value = var.vm_name
        }

        env {
          name  = "CLOUDFLARE_API_TOKEN"
          value = var.cloudflare_api_token
        }

        env {
          name  = "CLOUDFLARE_ZONE_ID"
          value = var.cloudflare_zone_id
        }

        env {
          name = "RCON_API_KEY"
          value = var.rcon_api_key
        }

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
      }

      container_concurrency = 10
      timeout_seconds       = 60
      service_account_name  = google_service_account.minecraft_vm.email
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_service.api.name
  location = google_cloud_run_service.api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
