#!/bin/bash
# Script pour lancer le client gamepad

echo "=== Launching Gamepad Client ==="

# Vérifie si le gamepad existe
if [ ! -e /dev/input/js0 ]; then
    echo "❌ Gamepad (/dev/input/js0) not found!"
    exit 1
fi

# Adresse IP du serveur (peut être passée en argument)
SERVER_IP="${1:-127.0.0.1}"

echo "Serveur: $SERVER_IP"

# Lance le conteneur Docker
sudo docker run -it --rm \
    --device /dev/input:/dev/input \
    --network host \
    --name gamepad-client \
    -v $(pwd)/config:/app/config:ro \
    gamepad2car-base python3 clients/gamepad_client.py --server-ip $SERVER_IP

