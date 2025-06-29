#!/bin/bash

# Script pour tester le programme avec un VESC réel
echo "=== Test avec VESC réel ==="

# Répertoire courant
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activation de l'environnement virtuel si présent
if [ -d "venv" ]; then
    echo "Activation de l'environnement virtuel..."
    source venv/bin/activate
fi

# Édition temporaire du fichier vescLib.py pour utiliser le VESC réel
echo "Configuration du mode réel dans vescLib.py..."
cp vescLib.py vescLib.py.backup
sed -i 's/USE_SIMULATION = True/USE_SIMULATION = False/' vescLib.py

# Compilation et exécution 
echo "Compilation et exécution du programme..."
./rebuild_and_test.sh

# Restauration du fichier original
echo "Restauration du fichier original..."
mv vescLib.py.backup vescLib.py
