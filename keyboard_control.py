import time
import traceback
from pyvesc_plus.VESC import VESC  # IMPORTANT: Utilise la bibliothèque pyvesc-plus
from pynput import keyboard

# --- CONFIGURATION ---
# Port série de votre VESC
SERIAL_PORT = '/dev/ttyACM0'
BAUDRATE = 115200

# Paramètres de contrôle du Robocar
# Puissance maximale du moteur (0.0 à 1.0). Commencez prudemment !
THROTTLE_MAX_POWER = 0.2
# Position du servo pour la direction.
# 0.0 = gauche, 0.5 = centre, 1.0 = droite.
# Ajustez si nécessaire pour que votre voiture aille droit.
STEERING_LEFT_LIMIT = 0.0
STEERING_RIGHT_LIMIT = 1.0
STEERING_CENTER_POS = 0.5
# --- FIN DE LA CONFIGURATION ---


class Robocar:
    """
    Une classe pour contrôler la voiture. Elle gère la connexion au VESC
    et fournit des méthodes simples pour le mouvement.
    """
    def __init__(self, port, baudrate, throttle_max, steering_left, steering_right, steering_center):
        """Initialise le Robocar avec ses paramètres."""
        self.port = port
        self.baudrate = baudrate
        self.vesc = None

        # Stocke les limites de fonctionnement
        self.throttle_max_power = throttle_max
        self.steering_left_limit = steering_left
        self.steering_right_limit = steering_right
        self.steering_center_pos = steering_center

        print("Robocar initialisé. Prêt à se connecter.")

    @property
    def is_connected(self):
        """Vérifie si le VESC est actuellement connecté."""
        return self.vesc is not None

    def connect(self):
        """Tente de se connecter au VESC."""
        if self.is_connected:
            print("Déjà connecté.")
            return True
        try:
            print(f"Connexion au VESC sur {self.port}...")
            # Le timeout est important pour ne pas bloquer le programme
            self.vesc = VESC(serial_port=self.port, baudrate=self.baudrate, timeout=0.1)
            fw_version = self.vesc.get_firmware_version()
            print(f"Connecté ! Version du Firmware: {fw_version}")
            return True
        except Exception as e:
            print("\nERREUR CRITIQUE LORS DE LA CONNEXION :")
            print(f"Détail: {e}")
            traceback.print_exc()
            self.vesc = None
            return False

    def disconnect(self):
        """Arrête tous les moteurs et se déconnecte proprement."""
        if self.is_connected:
            print("Arrêt d'urgence et déconnexion...")
            try:
                self.stop_motor()
                self.center_steering()
                self.vesc.close()
            except Exception as e:
                print(f"Erreur lors de la déconnexion: {e}")
            finally:
                self.vesc = None
                print("Déconnecté.")

    def set_throttle(self, value):
        """
        Définit la puissance du moteur.
        :param value: Une valeur entre -1.0 (marche arrière) et 1.0 (marche avant).
        """
        if not self.is_connected:
            return
        # Applique la limite de puissance configurée
        duty_cycle = self.throttle_max_power * value
        # Limite la valeur pour être sûr de ne pas dépasser les bornes
        duty_cycle = max(min(duty_cycle, self.throttle_max_power), -self.throttle_max_power)
        self.vesc.set_duty_cycle(duty_cycle)

    def set_steering(self, value):
        """
        Définit l'angle de direction.
        :param value: Une valeur entre -1.0 (gauche) et 1.0 (droite). 0 est le centre.
        """
        if not self.is_connected:
            return
        if value < 0: # Tourner à gauche
            # Interpole entre le centre (0) et la limite gauche (-1)
            servo_pos = self.steering_center_pos + value * (self.steering_center_pos - self.steering_left_limit)
        else: # Tourner à droite
            # Interpole entre le centre (0) et la limite droite (1)
            servo_pos = self.steering_center_pos + value * (self.steering_right_limit - self.steering_center_pos)

        self.vesc.set_servo(servo_pos)

    def stop_motor(self):
        """Méthode simple pour arrêter le moteur."""
        print("Moteur à l'arrêt")
        self.set_throttle(0)

    def center_steering(self):
        """Méthode simple pour remettre les roues droites."""
        print("Direction au centre")
        self.set_steering(0)


# --- GESTION DES ENTRÉES CLAVIER ---
# Note : la variable "car" est maintenant globale pour être accessible par les callbacks.
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


# --- PROGRAMME PRINCIPAL ---
if __name__ == "__main__":
    print("--- Programme de Contrôle Robocar ---")
    print("Utilisez les flèches pour vous déplacer.")
    print("Appuyez sur 'ESC' pour quitter.")
    print("--------------------------------------")

    # 1. Créer une instance de notre Robocar avec la configuration
    car = Robocar(
        port=SERIAL_PORT,
        baudrate=BAUDRATE,
        throttle_max=THROTTLE_MAX_POWER,
        steering_left=STEERING_LEFT_LIMIT,
        steering_right=STEERING_RIGHT_LIMIT,
        steering_center=STEERING_CENTER_POS
    )

    # 2. Tenter de se connecter
    if car.connect():
        print("\nLe contrôle est activé. C'est parti !")
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
