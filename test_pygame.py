#!/usr/bin/env python3
# test_pygame.py
import pygame
import sys
import os

# Désactiver les fonctionnalités problématiques
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["SDL_DBUS_SCREENSAVER_INHIBIT"] = "0"

print("Starting Pygame test...")
pygame.display.init()
print("Display initialized")
pygame.joystick.init()
print("Joystick initialized")

print(f"Joysticks available: {pygame.joystick.get_count()}")

pygame.quit()
print("Test completed successfully")