#!/bin/bash
# Script pour configurer l'environnement Python pour le VESC

echo "=== Configuration de l'environnement Python pour VESC ==="

VENV_PATH="./venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "Création d'un environnement virtuel Python..."
    /usr/local/bin/python3.10  -m venv "$VENV_PATH"
    if [ $? -ne 0 ]; then
        echo "Erreur lors de la création de l'environnement virtuel!"
        exit 1
    fi
    echo "Environnement virtuel créé avec succès"
fi

source "$VENV_PATH/bin/activate"
if [ $? -ne 0 ]; then
    echo "Erreur lors de l'activation de l'environnement virtuel!"
    exit 1
fi

echo "Installation des dépendances Python..."
cd PyVESC
/usr/local/bin/python3.10 -m pip install -r requirements.txt
/usr/local/bin/python3.10 -m pip install pyserial
if [ $? -ne 0 ]; then
    echo "Erreur lors de l'installation des dépendances!"
    exit 1
fi
