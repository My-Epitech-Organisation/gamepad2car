# Contenu de robocar_base.py

import traceback
import time
from pyvesc.VESC import VESC
import subprocess

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

        # Variables pour le lissage et la protection
        self.current_throttle = 0.0
        self.previous_throttle = 0.0
        self.max_throttle_change = 0.15
        self.throttle_filter_alpha = 0.7

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
                for i in range(5):
                    try:
                        self.set_throttle(self.current_throttle * (4-i)/5)
                        time.sleep(0.05)
                    except:
                        break

                self.stop_motor()
                self.center_steering()
                time.sleep(0.1)
                self.vesc.close()
            except Exception as e:
                print(f"Erreur lors de la déconnexion: {e}")
            finally:
                self.vesc = None
                self.current_throttle = 0.0
                self.previous_throttle = 0.0
                print("Déconnecté.")

    def set_throttle(self, value):
        """Définit la puissance du moteur avec lissage et protection (-1.0 à 1.0)."""
        if not self.is_connected: return

        # Borner la valeur d'entrée
        value = max(min(value, 1.0), -1.0)

        # Appliquer un filtre passe-bas pour lisser les changements brusques
        filtered_value = (self.throttle_filter_alpha * value + 
                         (1 - self.throttle_filter_alpha) * self.current_throttle)

        # Limiter le taux de changement pour éviter les pics de courant
        throttle_change = filtered_value - self.current_throttle
        if abs(throttle_change) > self.max_throttle_change:
            if throttle_change > 0:
                filtered_value = self.current_throttle + self.max_throttle_change
            else:
                filtered_value = self.current_throttle - self.max_throttle_change

        # Stocker la valeur actuelle pour la prochaine itération
        self.current_throttle = filtered_value

        # Calculer et envoyer la commande au VESC
        duty_cycle = self.throttle_max_power * filtered_value

        try:
            self.vesc.set_duty_cycle(duty_cycle)
        except Exception as e:
            print(f"Erreur lors de l'envoi de la commande moteur: {e}")
            # Tentative de reconnexion si la connexion est perdue
            if "Input/output error" in str(e):
                print("Connexion perdue, tentative de reconnexion...")
                self.disconnect()
                time.sleep(0.5)  # Pause avant reconnexion

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
        """Méthode simple pour arrêter le moteur progressivement."""
        # Arrêt progressif pour éviter les pics
        for i in range(5):
            try:
                self.set_throttle(self.current_throttle * (4-i)/5)
                time.sleep(0.02)
            except:
                break
        self.current_throttle = 0.0

    def emergency_stop(self):
        """Arrêt d'urgence immédiat (peut causer des pics de courant)."""
        if not self.is_connected: return
        try:
            self.vesc.set_duty_cycle(0)
            self.current_throttle = 0.0
        except Exception as e:
            print(f"Erreur lors de l'arrêt d'urgence: {e}")

    def center_steering(self):
        """Méthode simple pour remettre les roues droites."""
        self.set_steering(0)

    def set_throttle_smoothing(self, alpha=0.7, max_change=0.15):
        """Configure le lissage du throttle.
        
        Args:
            alpha: Coefficient de lissage (0.0 = très lisse, 1.0 = pas de lissage)
            max_change: Changement maximum par commande (0.0 à 1.0)
        """
        self.throttle_filter_alpha = max(0.0, min(1.0, alpha))
        self.max_throttle_change = max(0.01, min(1.0, max_change))
        print(f"Lissage configuré: alpha={self.throttle_filter_alpha}, max_change={self.max_throttle_change}")

    def get_throttle_status(self):
        """Retourne l'état actuel du throttle."""
        return {
            'current': self.current_throttle,
            'max_power': self.throttle_max_power,
            'smoothing_alpha': self.throttle_filter_alpha,
            'max_change': self.max_throttle_change
        }

    def incr_throttle_max(self):
        """Augmente la puissance maximale du moteur"""
        if self.throttle_max_power < 0.5:
            self.throttle_max_power += 0.1

    def decr_throttle_max(self):
        """Diminue la puissance maximale du moteur"""
        if self.throttle_max_power > 0.0:
            self.throttle_max_power -= 0.1

    def horn(self):
        """Active le klaxon."""
        if not self.is_connected: return
        try:
            subprocess.run(['/home/epitechrobocar/robocar/Sound-Robocar/startMusic.sh', '/home/epitechrobocar/robocar/Sound-Robocar/assets/circus_horn.wav'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Erreur lors de l'activation du klaxon: {e}")