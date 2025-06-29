#!/bin/bash

# Script pour tester le programme en mode simulation
echo "=== Test en mode simulation ==="

# Répertoire courant
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activation de l'environnement virtuel si présent
if [ -d "venv" ]; then
    echo "Activation de l'environnement virtuel..."
    source venv/bin/activate
fi

# Édition temporaire du fichier vescLib.py pour utiliser la simulation
echo "Configuration du mode simulation dans vescLib.py..."
cp vescLib.py vescLib.py.backup
sed -i 's/USE_SIMULATION = False/USE_SIMULATION = True/' vescLib.py

# Compilation et exécution 
echo "Compilation et exécution du programme..."
./rebuild_and_test.sh

# Restauration du fichier original
echo "Restauration du fichier original..."
mv vescLib.py.backup vescLib.py
