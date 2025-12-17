#!/bin/bash

apt update
apt install -y openjdk-17-jre-headless screen cron

mkdir -p /opt/minecraft
cd /opt/minecraft

wget https://launcher.mojang.com/v1/objects/<JAR_HASH>/server.jar
echo "eula=true" > eula.txt
