#!/bin/bash
# Script pour lancer le client gamepad

echo "=== Launching Gamepad Client ==="

# Vérifie si le gamepad existe
if [ ! -e /dev/input/js0 ]; then
    echo "❌ Gamepad (/dev/input/js0) not found!"
    exit 1
fi

# Lire l'IP du serveur depuis config/client_config.yaml ou utiliser argument
if [ -n "$1" ]; then
    SERVER_IP="$1"
elif [ -f config/client_config.yaml ]; then
    SERVER_IP=$(grep 'server_ip:' config/client_config.yaml | awk '{print $2}')
    echo "📝 IP du serveur depuis config: $SERVER_IP"
else
    SERVER_IP="127.0.0.1"
fi

echo "Serveur: $SERVER_IP"

# Lance le conteneur Docker (sans sudo pour éviter les problèmes de permissions)
# Le flag :z permet à Docker de relabeler les fichiers pour SELinux
# On lance Xvfb en arrière-plan puis le client pygame
docker run -it --rm \
    --device /dev/input:/dev/input \
    --network host \
    --name gamepad-client \
    -v $(pwd):/app:z \
    -w /app \
    gamepad2car-base bash -c "Xvfb :99 -screen 0 640x480x24 & export DISPLAY=:99 && sleep 1 && python3 clients/gamepad_client.py --server-ip $SERVER_IP"

