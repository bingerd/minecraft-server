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

# VM IAM Roles
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

resource "google_artifact_registry_repository_iam_member" "minecraft_image_pull" {
  project    = var.project_id
  location   = "europe-west1"
  repository = "minecraft-server"

  role   = "roles/artifactregistry.reader"
  member = "serviceAccount:${google_service_account.minecraft_vm.email}"
}

resource "google_project_iam_member" "minecraft_artifact_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.minecraft_vm.email}"
}


###########################
# Minecraft Container VM
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
      image = "cos-cloud/cos-stable"
      size  = 10
    }
  }

  network_interface {
    network       = "default"
    access_config {}
  }
  
  startup-script = <<-EOT
    #!/bin/bash
    # Install Google Cloud SDK on Container-Optimized OS
    set -e

    # Enable package manager
    sudo cos-extensions install cloud-sdk

    # Verify installation
    gcloud version

    echo "Google Cloud SDK installed successfully"
  EOT

  metadata = {
      # Enable Cloud Logging for COS
    google-logging-enabled = "true"

    gce-container-declaration = <<-EOT
      spec:
        containers:
          - name: minecraft
            image: "${var.minecraft_image}"
            env:
              - name: EULA
                value: "TRUE"
              - name: MEMORY
                value: "2G"
              - name: ENABLE_RCON
                value: "true"
              - name: RCON_PORT
                value: "25575"
              - name: RCON_PASSWORD
                value: "changeme"
            ports:
              - containerPort: 25565
              - containerPort: 25575
            stdin: false
            tty: false

        restartPolicy: Always
    EOT
  }

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
        "autoscaling.knative.dev/maxScale": "1"
        "run.googleapis.com/cpu-throttling": "false"
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

        # Set max instances
        resources {
          limits = {
            "cpu"    = "1"
            "memory" = "512Mi"
          }
        }
      }

      container_concurrency = 10
      timeout_seconds      = 60
      service_account_name = google_service_account.minecraft_vm.email

    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Allow unauthenticated access
resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_service.api.name
  location = google_cloud_run_service.api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
