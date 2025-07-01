"""
keyboard_control.py

Contrôle simple du Robocar via le clavier.
Utilise la classe Robocar avancée de robocar_base.py avec toutes ses fonctionnalités de sécurité.
"""

import time
from robocar_base import Robocar, ROBOCAR_CONFIG
from pynput import keyboard

# Variable globale pour la voiture
car = None

def on_press(key):
    """Callback appelé quand une touche est pressée."""
    if not car or not car.is_connected:
        return

    try:
        if key == keyboard.Key.up:
            print("Avancer")
            car.set_throttle(1.0)
        elif key == keyboard.Key.down:
            print("Reculer")
            car.set_throttle(-1.0)
        elif key == keyboard.Key.left:
            print("Gauche")
            car.set_steering(-1.0)
        elif key == keyboard.Key.right:
            print("Droite")
            car.set_steering(1.0)
        elif key.char == 'h':
            print("Klaxon !")
            car.horn()
        elif key.char == '+':
            car.incr_throttle_max()
        elif key.char == '-':
            car.decr_throttle_max()
        elif key.char == 's':
            print("Arrêt d'urgence !")
            car.emergency_stop()
    except AttributeError:
        # Touche spéciale sans attribut char
        pass
    except Exception as e:
        print(f"Erreur lors de l'envoi de la commande: {e}")
        if car:
            car.disconnect()

def on_release(key):
    """Callback appelé quand une touche est relâchée."""
    if not car or not car.is_connected:
        return

    if key in [keyboard.Key.up, keyboard.Key.down]:
        car.stop_motor()
    elif key in [keyboard.Key.left, keyboard.Key.right]:
        car.center_steering()

    if key == keyboard.Key.esc:
        print("Touche 'ESC' pressée, arrêt du programme...")
        return False # Ceci arrête le listener pynput


def main():
    """Fonction principale du programme de contrôle clavier."""
    global car
    
    print("--- Programme de Contrôle Robocar (Clavier) ---")
    print("Utilisez les flèches pour vous déplacer.")
    print("Touches disponibles :")
    print("  • ↑/↓ : Avancer/Reculer")
    print("  • ←/→ : Tourner gauche/droite")
    print("  • h : Klaxon")
    print("  • +/- : Augmenter/Diminuer vitesse max")
    print("  • s : Arrêt d'urgence")
    print("  • ESC : Quitter")
    print("----------------------------------------------")

    # 1. Créer une instance de notre Robocar avec la configuration
    car = Robocar(**ROBOCAR_CONFIG)

    # 2. Tenter de se connecter
    if car.connect():
        print("\nLe contrôle est activé. C'est parti !")
        
        # Configurer le lissage pour un contrôle plus doux
        car.set_throttle_smoothing(alpha=0.3, max_change=0.05)
        
        # Son d'accueil
        car.play_sound("assets/intro.wav")
        
        try:
            # 3. Démarrer l'écoute des touches du clavier
            with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                listener.join()
        except Exception as e:
            print(f"Une erreur est survenue pendant l'exécution: {e}")
        finally:
            # 4. S'assurer que tout est arrêté à la fin
            print("Fin de la boucle de contrôle.")
    else:
        print("\nImpossible de démarrer le contrôle. Vérifiez les erreurs ci-dessus.")

    # 5. La déconnexion est appelée quoi qu'il arrive
    if car:
        car.disconnect()

    print("Programme terminé proprement.")


if __name__ == "__main__":
    main()
