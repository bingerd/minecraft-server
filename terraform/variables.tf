variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "europe-west1"
}

variable "zone" {
  type    = string
  default = "europe-west1-b"
}

variable "vm_name" {
  type    = string
  default = "minecraft-server"
}

variable "minecraft_image" {
  description = "Full Artifact Registry image URL"
  type        = string
}

variable "api_image" {
  description = "Full Artifact Registry image URL"
  type        = string
}

variable "billing_account_id" {
  type        = string
  description = "Billing account ID for budget alerts"
}

variable "monthly_budget" {
  type        = number
  description = "Monthly budget in USD"
  default     = 5
}
