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

# ===============================
# Billing / Budget
# ===============================
variable "billing_account_id" {
  type        = string
  description = "Billing account ID for budget alerts"
}

variable "monthly_budget" {
  type        = number
  description = "Monthly budget in EUR"
  default     = 5
}

# ===============================
# GitHub Actions WIF
# ===============================
variable "github_repo_id" {
  type        = string
  description = "GitHub repository ID for WIF access (immutable)"
}

variable "github_org_repo" {
  type        = string
  description = "GitHub org/repo (for reference)"
}

# ===============================
# Optional: Email for billing notifications
# ===============================
variable "billing_email" {
  type        = string
  description = "Email to receive billing alerts"
  default     = "bing.1998.tan@hotmail.com"
}
