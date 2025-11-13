#!/bin/bash
# Script pour lancer le serveur Robocar

echo "=== Launching Robocar Server ==="

# Vérifie si le VESC est bien branché
if [ ! -e /dev/ttyACM0 ]; then
    echo "❌ VESC (/dev/ttyACM0) not found!"
    exit 1
fi

# Prépare le socket PulseAudio si dispo
if [ -z "$XDG_RUNTIME_DIR" ]; then
    export XDG_RUNTIME_DIR="/run/user/$(id -u)"
fi
export PULSE_SERVER=unix:${XDG_RUNTIME_DIR}/pulse/native

# Lance le conteneur Docker
sudo docker run -it --rm \
    --device /dev/ttyACM0:/dev/ttyACM0 \
    --device /dev/snd \
    --network host \
    --group-add $(getent group audio | cut -d: -f3) \
    --name robocar-server \
    -v $(pwd)/config:/app/config:ro \
    -v $(pwd)/logs:/app/logs \
    gamepad2car-base python3 server/robocar_server.py

