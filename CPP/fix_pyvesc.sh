#!/bin/bash

# Script pour corriger le module PyVESC
echo "=== Correction du module PyVESC pour le VESC réel ==="

# Répertoire courant
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Trouver le fichier VESC.py
VESC_FILE=$(find PyVESC -name "VESC.py" | grep -v __pycache__ | head -n 1)

if [ -z "$VESC_FILE" ]; then
    echo "Erreur: Impossible de trouver le fichier VESC.py"
    exit 1
fi

echo "Fichier VESC.py trouvé: $VESC_FILE"

# Créer une sauvegarde
cp "$VESC_FILE" "${VESC_FILE}.backup"

# Vérifier le contenu
echo -e "\nContenu actuel (premières lignes) :"
head -n 20 "$VESC_FILE"

# Modifier le fichier pour ajouter l'importation manquante
echo -e "\nAjout des importations nécessaires..."

# Ajouter l'importation au début du fichier
sed -i '1s/^/import sys\nsys.path.append("../..")\nfrom pyvesc.protocol import *\n\n/' "$VESC_FILE"

echo -e "\nContenu après modification (premières lignes) :"
head -n 20 "$VESC_FILE"

echo -e "\nVérification des autres fichiers pour 'pyvesc' non importé..."
grep -r "pyvesc\." --include="*.py" PyVESC --color

echo -e "\nCorrection terminée. Maintenant vous pouvez tester avec le VESC réel."
echo "Utilisez la commande :"
echo "cd $SCRIPT_DIR && ./rebuild_and_test.sh"
