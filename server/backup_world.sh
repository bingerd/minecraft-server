#!/bin/bash

WORLD_DIR="/data/world"
BUCKET_NAME="${BUCKET_NAME:?BUCKET_NAME is required}"
DATE=$(date +%Y%m%d_%H%M%S)

echo "Starting backup of Minecraft world..."
tar -czf /tmp/minecraft_world_backup_$DATE.tar.gz -C "$WORLD_DIR" .
gsutil cp /tmp/minecraft_world_backup_$DATE.tar.gz gs://$BUCKET_NAME/minecraft_world_backup_$DATE.tar.gz