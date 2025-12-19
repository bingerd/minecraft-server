terraform {
  backend "gcs" {
    bucket = "bingerd-minecraft-server"
    prefix = "tf-state"
  }
}
