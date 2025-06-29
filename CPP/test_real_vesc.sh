#!/bin/bash

# Script pour tester la connexion au VESC en mode réel
echo "=== Test de connexion au VESC réel ==="

# Trouver tous les périphériques ttyACM* et ttyUSB*
echo "Périphériques série disponibles :"
ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || echo "Aucun périphérique série détecté"

# Vérifier les droits d'accès
echo -e "\nVérification des droits d'accès aux ports série :"
getent group dialout | grep $(whoami) > /dev/null
if [ $? -eq 0 ]; then
    echo "Utilisateur $(whoami) fait partie du groupe dialout - OK"
else
    echo "ATTENTION: L'utilisateur $(whoami) ne fait PAS partie du groupe dialout"
    echo "Exécutez la commande suivante pour ajouter l'utilisateur au groupe dialout:"
    echo "sudo usermod -a -G dialout $(whoami)"
    echo "Puis déconnectez-vous et reconnectez-vous pour que les changements prennent effet."
fi

# Compiler et exécuter le programme avec USE_SIMULATION=False
echo -e "\n=== Compilation pour le mode VESC réel ==="
echo "Modification temporaire du fichier vescLib.py pour désactiver la simulation..."

# Sauvegarder le fichier original
cp vescLib.py vescLib.py.backup

# Modifier la variable USE_SIMULATION
sed -i 's/USE_SIMULATION = True/USE_SIMULATION = False/' vescLib.py

# Vérifier si la modification a réussi
grep "USE_SIMULATION" vescLib.py

echo -e "\n=== Compilation et exécution ==="
./rebuild_and_test.sh

# Restaurer le fichier original
mv vescLib.py.backup vescLib.py

echo -e "\n=== Test terminé ==="
echo "Si vous ne voyez pas de mouvement, vérifiez :"
echo "1. Que le VESC est alimenté"
echo "2. Que le port série est correct (/dev/ttyACM0 ou autre)"
echo "3. Que la valeur max_duty_cycle (actuellement 0.3 ou 30%) est suffisante"
echo "4. Que les droits d'accès sont corrects (groupe dialout)"
