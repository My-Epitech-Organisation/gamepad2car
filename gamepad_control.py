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
STEERING_AXIS = 0  # Joystick GAUCHE, axe horizontal
REVERSE_AXIS = 2   # Gâchette GAUCHE (LT)
FORWARD_AXIS = 5   # Gâchette DROITE (RT)

# Boutons
EXIT_BUTTON = 8    # Bouton "Start" ou "Logitech"
KLAXON_BUTTON = 3   # Bouton Y (Klaxon)
SPEED_DOWN = 4
SPEED_UP = 5

# Zone morte pour la direction afin d'aller bien droit
JOYSTICK_DEADZONE = 0.1
# Seuil de détection de changement brusque de throttle (plus sensible)
THROTTLE_CHANGE_THRESHOLD = 0.15  # Réduit de 0.3 à 0.15
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
    print(f"Direction : Joystick GAUCHE (gauche/droite)")
    print(f"Klaxon : Bouton Y (bouton 3)")
    print(f"Epitech : Bouton UP (bouton le D-Pad UP)")
    print(f"Satelisation : Bouton DOWN (bouton le D-Pad DOWN)")
    print(f"Peter : Bouton RIGHT (bouton le D-Pad RIGHT)")
    print(f"Polizia : Bouton LEFT (bouton le D-Pad LEFT)")
    print(f"APPUYER pour quitter : Bouton 'Start' (bouton 8)")
    print("-------------------------------------------\n")

    car = Robocar(**ROBOCAR_CONFIG)

    try:
        if not car.connect():
            print("Impossible de démarrer. Vérifiez la connexion VESC.")
            return

        car.set_throttle_smoothing(alpha=0.2, max_change=0.03)

        running = True
        car.play_sound("assets/intro.wav")
        while running:
            # Vérifier si la connexion est perdue (OVP alimentation)
            if hasattr(car, 'connection_lost') and car.connection_lost:
                print(f"\n🔌 Connexion perdue - Alimentation probablement en OVP")
                print("Arrêt du programme pour éviter les erreurs série.")
                break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.JOYBUTTONDOWN and event.button == EXIT_BUTTON:
                    print("\nBouton de sortie détecté. Arrêt...")
                    running = False
                if event.type == pygame.JOYBUTTONUP:
                    if event.button == SPEED_DOWN:
                        car.decr_throttle_max()
                    if event.button == SPEED_UP:
                        car.incr_throttle_max()
                if joystick.get_button(KLAXON_BUTTON):
                    car.horn()
                if joystick.get_numhats() > 0:
                    hat_x, hat_y = joystick.get_hat(0)
                    if hat_y == 1:
                        car.play_sound("assets/EpitechPassion.wav")
                    elif hat_y == -1:
                        car.play_sound("assets/Satelisation.wav")
                    elif hat_x == 1:
                        car.play_sound("assets/Peter.wav")
                    elif hat_x == -1:
                        car.play_sound("assets/Polizia.wav")

            # 1. Lire la direction depuis le joystick DROIT
            steering_value = joystick.get_axis(STEERING_AXIS)
            if abs(steering_value) < JOYSTICK_DEADZONE:
                steering_value = 0.0

            # 2. Lire les gâchettes et les convertir en [0.0, 1.0]
            forward_power = (joystick.get_axis(FORWARD_AXIS) + 1) / 2
            reverse_power = (joystick.get_axis(REVERSE_AXIS) + 1) / 2

            # 3. Calculer l'accélération finale
            throttle_value = forward_power - reverse_power

            # 4. Afficher les valeurs en temps réel avec statut de protection
            print(f"Accél: {throttle_value:>6.2f} | Dir: {steering_value:>5.2f} | Max: {car.throttle_max_power:.1f}", end="\r")

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
