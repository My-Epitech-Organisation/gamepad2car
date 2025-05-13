#!/usr/bin/env python3
# test_pygame.py
import pygame
import sys
import os

# Désactiver les fonctionnalités problématiques
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["SDL_DBUS_SCREENSAVER_INHIBIT"] = "0"
os.environ["SDL_VIDEODRIVER"] = "dummy"  # Utiliser un pilote d'affichage factice

print("Starting Pygame test...")
try:
    # Initialiser uniquement les sous-systèmes nécessaires
    pygame.joystick.init()
    print("Joystick initialized")
    
    # Vérifier les joysticks disponibles
    print(f"Joysticks available: {pygame.joystick.get_count()}")
    
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print(f"Connected to: {joystick.get_name()}")
        print(f"Number of axes: {joystick.get_numaxes()}")
        print(f"Number of buttons: {joystick.get_numbuttons()}")
finally:
    pygame.quit()
    print("Test completed successfully")