# ===============================
# Project & Region / Zone
# ===============================
variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  description = "GCP Region"
  default     = "europe-west1"
}

variable "zone" {
  type        = string
  description = "GCP Zone"
  default     = "europe-west1-b"
}

variable "vm_name" {
  type        = string
  description = "Name of the Minecraft VM"
  default     = "minecraft-server"
}

# ===============================
# Docker Images
# ===============================
variable "minecraft_image" {
  description = "Full Artifact Registry image URL for the Minecraft server"
  type        = string
}

variable "api_image" {
  description = "Full Artifact Registry image URL for the Cloud Run API"
  type        = string
}
