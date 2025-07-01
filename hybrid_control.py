# contenu de hybrid_control.py

import pygame
import time
import socket
import threading
from robocar_base import Robocar, ROBOCAR_CONFIG

# --- CONFIGURATION MANETTE ET SERVEUR ---
# Manette (vérifiez vos bindings si nécessaire)
STEERING_AXIS = 3
REVERSE_AXIS = 2
FORWARD_AXIS = 5
TOGGLE_MODE_BUTTON = 0  # Bouton 'X' sur une F710 en mode XInput
EXIT_BUTTON = 8
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
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    server_thread = AICommandServer(UDP_HOST, UDP_PORT)
    server_thread.start()

    print(f"Manette détectée : {joystick.get_name()}")
    print("\n--- CONTRÔLE HYBRIDE ACTIF ---")
    print("MODE PAR DÉFAUT : MANUEL")
    print("Appuyez sur le bouton 'X' (bouton 0) pour basculer en mode AUTONOME.")
    print("--------------------------------\n")

    control_mode = 'MANUAL' # Mode de contrôle initial

    try:
        if not car.connect():
            raise RuntimeError("Impossible de se connecter au VESC.")

        running = True
        while running:
            # 2. Gérer les événements de la manette
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == EXIT_BUTTON:
                        running = False
                    if event.button == TOGGLE_MODE_BUTTON:
                        if control_mode == 'MANUAL':
                            control_mode = 'AUTO'
                            # Sécurité : on remet à zéro les commandes au moment du switch
                            car.stop_motor()
                            car.center_steering()
                        else:
                            control_mode = 'MANUAL'
                        print(f"\n--- MODE CHANGÉ EN: {control_mode} ---")

            # 3. Appliquer les commandes en fonction du mode
            if control_mode == 'MANUAL':
                # Lire les commandes de la manette
                forward = (joystick.get_axis(FORWARD_AXIS) + 1) / 2
                reverse = (joystick.get_axis(REVERSE_AXIS) + 1) / 2
                throttle_cmd = forward - reverse
                steering_cmd = joystick.get_axis(STEERING_AXIS)
                if abs(steering_cmd) < JOYSTICK_DEADZONE: steering_cmd = 0.0

            else: # control_mode == 'AUTO'
                # Lire la dernière commande de l'IA (de manière thread-safe)
                with command_lock:
                    throttle_cmd = ai_command['throttle']
                    steering_cmd = ai_command['steering']

            # 4. Envoyer les commandes finales au Robocar
            car.set_throttle(throttle_cmd)
            car.set_steering(steering_cmd)

            print(f"Mode: {control_mode:6} | Accél: {throttle_cmd:>6.2f} | Dir: {steering_cmd:>5.2f}", end='\r')
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