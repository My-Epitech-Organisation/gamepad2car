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
SPEED_DOWN = 4
SPEED_UP = 5

# Zone morte pour la direction afin d'aller bien droit
JOYSTICK_DEADZONE = 0.1
# Seuil de détection de changement brusque de throttle
THROTTLE_CHANGE_THRESHOLD = 0.3
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
    print(f"APPUYER pour quitter : Bouton 'Start' (bouton 8)")
    print("-------------------------------------------\n")

    car = Robocar(**ROBOCAR_CONFIG)

    previous_throttle = 0.0
    sudden_change_count = 0

    try:
        if not car.connect():
            print("Impossible de démarrer. Vérifiez la connexion VESC.")
            return

        car.set_throttle_smoothing(alpha=0.6, max_change=0.12)
        print("Lissage de protection activé pour éviter les pics de courant.\n")

        running = True
        while running:
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

            # 1. Lire la direction depuis le joystick DROIT
            steering_value = joystick.get_axis(STEERING_AXIS)
            if abs(steering_value) < JOYSTICK_DEADZONE:
                steering_value = 0.0

            # 2. Lire les gâchettes et les convertir en [0.0, 1.0]
            forward_power = (joystick.get_axis(FORWARD_AXIS) + 1) / 2
            reverse_power = (joystick.get_axis(REVERSE_AXIS) + 1) / 2

            # 3. Calculer l'accélération finale
            throttle_value = forward_power - reverse_power

            # 4. Détecter les changements brusques qui peuvent causer des pics
            throttle_change = abs(throttle_value - previous_throttle)
            if throttle_change > THROTTLE_CHANGE_THRESHOLD:
                sudden_change_count += 1
                if sudden_change_count > 3:  # Plus de 3 changements brusques
                    print(f"\n⚠️  ATTENTION: Changements brusques détectés! Réduisez la vitesse de manœuvre.")
                    sudden_change_count = 0  # Reset du compteur
            else:
                sudden_change_count = max(0, sudden_change_count - 1)  # Diminue progressivement

            # 5. Afficher les valeurs en temps réel avec statut de protection
            status_icon = "🔒" if throttle_change > THROTTLE_CHANGE_THRESHOLD else "✅"
            print(f"{status_icon} Accél: {throttle_value:>6.2f} | Dir: {steering_value:>5.2f} | Max: {car.throttle_max_power:.1f}", end="\r")

            # 6. Envoyer les commandes à la voiture
            car.set_throttle(throttle_value)
            car.set_steering(steering_value)
            
            previous_throttle = throttle_value
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
