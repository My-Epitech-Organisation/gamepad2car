# contenu de hybrid_control.py

import pygame
import time
import socket
import threading
from robocar_base import Robocar, ROBOCAR_CONFIG

# --- CONFIGURATION MANETTE ET SERVEUR ---
# Manette (vérifiez vos bindings si nécessaire)
STEERING_AXIS = 0  # Joystick GAUCHE, axe horizontal
REVERSE_AXIS = 2   # Gâchette GAUCHE (LT)
FORWARD_AXIS = 5   # Gâchette DROITE (RT)
TOGGLE_MODE_BUTTON = 0  # Bouton 'X' pour basculer manuel/auto
EXIT_BUTTON = 8    # Bouton "Start" ou "Logitech"
KLAXON_BUTTON = 3  # Bouton Y (Klaxon)
SPEED_DOWN = 4     # Bouton LB (diminuer vitesse max)
SPEED_UP = 5       # Bouton RB (augmenter vitesse max)
JOYSTICK_DEADZONE = 0.1

# Serveur UDP
UDP_HOST = '127.0.0.1'
UDP_PORT = 12345
# ----------------------------------------

# Variable globale partagée entre les threads pour stocker la dernière commande de l'IA
# Le lock est essentiel pour éviter les problèmes d'accès concurrentiel
ai_command = {'throttle': 0.0, 'steering': 0.0}
command_lock = threading.Lock()

class AICommandServer(threading.Thread):
    """Un thread serveur qui écoute les commandes UDP en arrière-plan."""
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = False

    def run(self):
        """La boucle principale du thread."""
        self.sock.bind((self.host, self.port))
        self.running = True
        print(f"[Serveur UDP] En écoute sur udp://{self.host}:{self.port}")

        while self.running:
            try:
                data, _ = self.sock.recvfrom(1024)
                message = data.decode()
                parts = message.split(';')
                if len(parts) == 2:
                    # On met à jour la commande partagée de manière thread-safe
                    with command_lock:
                        ai_command['throttle'] = float(parts[0])
                        ai_command['steering'] = float(parts[1])
            except Exception:
                # Si le socket est fermé pendant qu'on attend, une exception est levée
                pass # On l'ignore pour quitter proprement

        print("[Serveur UDP] Thread terminé.")

    def stop(self):
        """Signal pour arrêter le thread."""
        self.running = False
        # Astuce pour débloquer sock.recvfrom() qui attend
        self.sock.close()


def main():
    """Fonction principale du programme de contrôle hybride."""
    # 1. Initialiser le Robocar, Pygame et le serveur UDP
    car = Robocar(**ROBOCAR_CONFIG)

    pygame.init()
    pygame.joystick.init()
    
    if pygame.joystick.get_count() == 0:
        print("ERREUR: Aucune manette détectée.")
        return
        
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    server_thread = AICommandServer(UDP_HOST, UDP_PORT)
    server_thread.start()

    print(f"Manette détectée : {joystick.get_name()}")
    print("\n--- CONTRÔLE HYBRIDE ACTIF ---")
    print("MODE PAR DÉFAUT : MANUEL")
    print("Contrôles manuels :")
    print(f"  • Accélération : Gâchette DROITE (RT)")
    print(f"  • Marche arrière/Frein : Gâchette GAUCHE (LT)")
    print(f"  • Direction : Joystick GAUCHE (gauche/droite)")
    print(f"  • Klaxon : Bouton Y (bouton {KLAXON_BUTTON})")
    print(f"  • Vitesse - : Bouton LB (bouton {SPEED_DOWN})")
    print(f"  • Vitesse + : Bouton RB (bouton {SPEED_UP})")
    print(f"  • Sons : D-Pad (haut/bas/gauche/droite)")
    print(f"Appuyez sur le bouton 'X' (bouton {TOGGLE_MODE_BUTTON}) pour basculer en mode AUTONOME.")
    print(f"Appuyez sur 'Start' (bouton {EXIT_BUTTON}) pour quitter.")
    print("--------------------------------\n")

    control_mode = 'MANUAL' # Mode de contrôle initial
    previous_hat = (0, 0)   # Pour détecter les changements du D-Pad

    try:
        if not car.connect():
            raise RuntimeError("Impossible de se connecter au VESC.")

        # Configurer le lissage pour un contrôle plus doux
        car.set_throttle_smoothing(alpha=0.2, max_change=0.03)
        
        # Son d'accueil
        car.play_sound("assets/intro.wav")

        running = True
        while running:
            # Vérifier si la connexion est perdue (OVP alimentation)
            if hasattr(car, 'connection_lost') and car.connection_lost:
                print(f"\n🔌 Connexion perdue - Alimentation probablement en OVP")
                print("Arrêt du programme pour éviter les erreurs série.")
                break

            # 2. Gérer les événements de la manette
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == EXIT_BUTTON:
                        running = False
                    elif event.button == TOGGLE_MODE_BUTTON:
                        if control_mode == 'MANUAL':
                            control_mode = 'AUTO'
                            # Sécurité : on remet à zéro les commandes au moment du switch
                            car.stop_motor()
                            car.center_steering()
                        else:
                            control_mode = 'MANUAL'
                        print(f"\n--- MODE CHANGÉ EN: {control_mode} ---")
                elif event.type == pygame.JOYBUTTONUP:
                    if event.button == SPEED_DOWN:
                        car.decr_throttle_max()
                    elif event.button == SPEED_UP:
                        car.incr_throttle_max()

            # Gestion du klaxon (maintien du bouton)
            if joystick.get_button(KLAXON_BUTTON):
                car.horn()

            # Gestion des sons via D-Pad
            if joystick.get_numhats() > 0:
                hat_x, hat_y = joystick.get_hat(0)
                if (hat_x, hat_y) != previous_hat:
                    if hat_y == 1:  # D-Pad haut
                        car.play_sound("assets/EpitechPassion.wav")
                    elif hat_y == -1:  # D-Pad bas
                        car.play_sound("assets/Satelisation.wav")
                    elif hat_x == 1:  # D-Pad droite
                        car.play_sound("assets/Peter.wav")
                    elif hat_x == -1:  # D-Pad gauche
                        car.play_sound("assets/Polizia.wav")
                    previous_hat = (hat_x, hat_y)

            # 3. Appliquer les commandes en fonction du mode
            if control_mode == 'MANUAL':
                # Lire les commandes de la manette
                forward = (joystick.get_axis(FORWARD_AXIS) + 1) / 2
                reverse = (joystick.get_axis(REVERSE_AXIS) + 1) / 2
                throttle_cmd = forward - reverse
                steering_cmd = joystick.get_axis(STEERING_AXIS)
                if abs(steering_cmd) < JOYSTICK_DEADZONE: 
                    steering_cmd = 0.0

            else: # control_mode == 'AUTO'
                # Lire la dernière commande de l'IA (de manière thread-safe)
                with command_lock:
                    throttle_cmd = ai_command['throttle']
                    steering_cmd = ai_command['steering']

            # 4. Envoyer les commandes finales au Robocar
            car.set_throttle(throttle_cmd)
            car.set_steering(steering_cmd)

            # Affichage enrichi avec vitesse max
            print(f"Mode: {control_mode:6} | Accél: {throttle_cmd:>6.2f} | Dir: {steering_cmd:>5.2f} | Max: {car.throttle_max_power:.1f}", end='\r')
            time.sleep(0.02)

    except Exception as e:
        print(f"\nUne erreur critique est survenue: {e}")
    finally:
        # 5. Nettoyage propre
        print("\n\n--- Arrêt des systèmes ---")
        if server_thread.is_alive():
            print("Arrêt du serveur UDP...")
            server_thread.stop()
            server_thread.join() # Attendre que le thread se termine

        if car and car.is_connected:
            car.disconnect()

        pygame.quit()
        print("Programme terminé proprement.")


if __name__ == "__main__":
    main()