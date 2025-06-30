"""
gamepad_control.py

Ce script pilote le Robocar en utilisant une manette de jeu (style F710).
Il utilise une configuration de type "jeu de course" avec les gâchettes pour
l'accélération et le joystick droit pour la direction.
"""

import pygame
import time
from robocar_base import Robocar, ROBOCAR_CONFIG

# --- CONFIGURATION DE LA MANETTE (Style "Jeu de Course") ---
# Axes (VÉRIFIEZ AVEC LE SCRIPT DE DIAGNOSTIC !)
STEERING_AXIS = 3  # Joystick DROIT, axe horizontal
REVERSE_AXIS = 2   # Gâchette GAUCHE (LT)
FORWARD_AXIS = 5   # Gâchette DROITE (RT)

# Boutons
EXIT_BUTTON = 8    # Bouton "Start" ou "Logitech"

# Zone morte pour la direction afin d'aller bien droit
JOYSTICK_DEADZONE = 0.1
# --------------------------------------------------------

def main():
    """Fonction principale du programme."""
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("ERREUR: Aucune manette détectée.")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Manette détectée : {joystick.get_name()}")
    print("\n--- CONTRÔLES ACTIFS (Style Course v2) ---")
    print(f"Accélération : Gâchette DROITE (RT)")
    print(f"Marche arrière/Frein : Gâchette GAUCHE (LT)")
    print(f"Direction : Joystick DROIT (gauche/droite)")
    print(f"APPUYER pour quitter : Bouton 'Start' (bouton 8)")
    print("-------------------------------------------\n")

    car = Robocar(**ROBOCAR_CONFIG)
    
    try:
        if not car.connect():
            print("Impossible de démarrer. Vérifiez la connexion VESC.")
            return

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.JOYBUTTONDOWN and event.button == EXIT_BUTTON:
                    print("\nBouton de sortie détecté. Arrêt...")
                    running = False

            # 1. Lire la direction depuis le joystick DROIT
            steering_value = joystick.get_axis(STEERING_AXIS)
            if abs(steering_value) < JOYSTICK_DEADZONE:
                steering_value = 0.0

            # 2. Lire les gâchettes et les convertir en [0.0, 1.0]
            forward_power = (joystick.get_axis(FORWARD_AXIS) + 1) / 2
            reverse_power = (joystick.get_axis(REVERSE_AXIS) + 1) / 2
            
            # 3. Calculer l'accélération finale
            throttle_value = forward_power - reverse_power

            # 4. Afficher les valeurs en temps réel
            print(f"Accélération: {throttle_value:>6.2f} | Direction: {steering_value:>5.2f}", end='\r')

            # 5. Envoyer les commandes à la voiture
            car.set_throttle(throttle_value)
            car.set_steering(steering_value)

            time.sleep(0.02)

    except Exception as e:
        print(f"\nUne erreur inattendue est survenue: {e}")
    finally:
        print("\n") 
        if car and car.is_connected:
            car.disconnect()
        pygame.quit()
        print("Programme terminé proprement.")


if __name__ == "__main__":
    main()