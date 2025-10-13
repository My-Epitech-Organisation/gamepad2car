#!/bin/bash
echo "=== Launching Gamepad2Car with Audio Support ==="

# Vérifie si le device du gamepad existe
if [ ! -e /dev/input/js0 ]; then
    echo "❌ Gamepad (/dev/input/js0) not found!"
    exit 1
fi

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
    --device /dev/input:/dev/input \
    --device /dev/snd \
    --group-add $(getent group audio | cut -d: -f3) \
    gamepad2car-base python3 gamepad_control.py
