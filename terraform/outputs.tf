output "minecraft_server_ip" {
  description = "Public IP of the Minecraft server VM"
  value       = google_compute_instance.minecraft.network_interface[0].access_config[0].nat_ip
}

output "minecraft_disk_name" {
  value = google_compute_disk.minecraft_disk.name
}
