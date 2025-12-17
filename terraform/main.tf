provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Optional persistent disk
resource "google_compute_disk" "minecraft_disk" {
  name  = "${var.vm_name}-disk"
  type  = "pd-standard"
  zone  = var.zone
  size  = 10 # GB
}

# Compute Engine VM
resource "google_compute_instance" "minecraft" {
  name         = var.vm_name
  machine_type = "e2-micro" # free-tier eligible
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 10
    }
  }

  attached_disk {
    source = google_compute_disk.minecraft_disk.id
  }

  network_interface {
    network = "default"
    access_config {} # External IP
  }

  tags = ["minecraft-server"]

  # No startup-script to keep VM clean for testing
}

# Firewall to allow Minecraft connections
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
