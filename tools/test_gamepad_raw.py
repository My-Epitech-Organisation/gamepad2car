#!/usr/bin/env python3
"""
Script de diagnostic pour voir les valeurs RAW de la manette.
Utile pour débugger les problèmes de contrôle.
"""

import pygame
import time

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("❌ Aucune manette détectée")
    exit(1)

joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"🎮 Manette: {joystick.get_name()}")
print(f"   Axes: {joystick.get_numaxes()}")
print(f"   Boutons: {joystick.get_numbuttons()}")
print(f"   Hats: {joystick.get_numhats()}")
print("\n" + "="*60)
print("Valeurs en temps réel (Ctrl+C pour quitter):")
print("="*60 + "\n")

# Configuration du client
STEERING_AXIS = 0
REVERSE_AXIS = 2
FORWARD_AXIS = 5
JOYSTICK_DEADZONE = 0.1

screen = pygame.display.set_mode((100, 100))

try:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise KeyboardInterrupt
        
        # Lire axes raw
        steering_raw = joystick.get_axis(STEERING_AXIS)
        reverse_raw = joystick.get_axis(REVERSE_AXIS)
        forward_raw = joystick.get_axis(FORWARD_AXIS)
        
        # Calculer comme dans le client
        steering_value = steering_raw if abs(steering_raw) >= JOYSTICK_DEADZONE else 0.0
        forward_power = (forward_raw + 1) / 2
        reverse_power = (reverse_raw + 1) / 2
        throttle_value = forward_power - reverse_power
        
        # Afficher
        print(f"\r"
              f"Steering: {steering_raw:>6.2f} → {steering_value:>6.2f} | "
              f"Forward(RT): {forward_raw:>6.2f} → {forward_power:>5.2f} | "
              f"Reverse(LT): {reverse_raw:>6.2f} → {reverse_power:>5.2f} | "
              f"Throttle: {throttle_value:>6.2f}",
              end="")
        
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n\n✅ Arrêt")
    
finally:
    pygame.quit()
