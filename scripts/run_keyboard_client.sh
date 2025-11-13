#!/bin/bash
# Script pour lancer le client clavier

echo "=== Launching Keyboard Client ==="

# Adresse IP du serveur (peut être passée en argument)
SERVER_IP="${1:-127.0.0.1}"

echo "Serveur: $SERVER_IP"

# Lance le conteneur Docker
sudo docker run -it --rm \
    --network host \
    --name keyboard-client \
    -v $(pwd)/config:/app/config:ro \
    -v /dev/input:/dev/input:ro \
    --privileged \
    gamepad2car-base python3 clients/keyboard_client.py --server-ip $SERVER_IP

