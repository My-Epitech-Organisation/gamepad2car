# Contenu de robocar_base.py

import traceback
from pyvesc.VESC import VESC

# --- CONFIGURATION GLOBALE DU ROBOCAR ---
# Regroupe tous les paramètres pour une importation facile
ROBOCAR_CONFIG = {
    'port': '/dev/ttyACM0',
    'baudrate': 115200,
    'throttle_max': 0.1, # Puissance max moteur (0.0 à 1.0)
    'steering_left': 0.0,
    'steering_right': 1.0,
    'steering_center': 0.5
}
# ----------------------------------------

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
            self.vesc = VESC(serial_port=self.port, baudrate=self.baudrate, timeout=0.5)
            fw_version = self.vesc.get_firmware_version()
            print(f"Connecté ! Version du Firmware: {fw_version}")
            return True
        except Exception as e:
            print(f"\nERREUR CRITIQUE LORS DE LA CONNEXION : {e}")
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
        """Définit la puissance du moteur (-1.0 à 1.0)."""
        if not self.is_connected: return
        duty_cycle = self.throttle_max_power * max(min(value, 1.0), -1.0)
        self.vesc.set_duty_cycle(duty_cycle)

    def set_steering(self, value):
        """Définit l'angle de direction (-1.0 à 1.0)."""
        if not self.is_connected: return
        value = max(min(value, 1.0), -1.0) # borner la valeur
        if value < 0:
            servo_pos = self.steering_center_pos + value * (self.steering_center_pos - self.steering_left_limit)
        else:
            servo_pos = self.steering_center_pos + value * (self.steering_right_limit - self.steering_center_pos)
        self.vesc.set_servo(servo_pos)

    def stop_motor(self):
        """Méthode simple pour arrêter le moteur."""
        self.set_throttle(0)

    def center_steering(self):
        """Méthode simple pour remettre les roues droites."""
        self.set_steering(0)

    def incr_throttle_max(self):
        """Augmente la puissance maximale du moteur"""
        if self.throttle_max_power < 1.0:
            self.throttle_max_power += 0.1

    def decr_throttle_max(self):
        """Diminue la puissance maximale du moteur"""
        if self.throttle_max_power > 0.0:
            self.throttle_max_power -= 0.1
