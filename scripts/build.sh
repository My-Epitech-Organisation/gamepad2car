#!/bin/bash
# Script pour construire l'image Docker

echo "=== Building Robocar Docker Image ==="
docker build -f Dockerfile.base -t gamepad2car-base .

if [ $? -eq 0 ]; then
    echo "✅ Image gamepad2car-base construite avec succès!"
else
    echo "❌ Erreur lors de la construction de l'image"
    exit 1
fi
