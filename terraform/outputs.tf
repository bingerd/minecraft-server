output "minecraft_ip" {
  value = google_compute_instance.minecraft.network_interface[0].access_config[0].nat_ip
}

output "api_url" {
  value = google_cloud_run_service.api.status[0].url
}
