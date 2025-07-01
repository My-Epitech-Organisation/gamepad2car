# Contenu de robocar_base.py

import traceback
import time
from pyvesc.VESC import VESC
import subprocess

# --- CONFIGURATION GLOBALE DU ROBOCAR ---
# Regroupe tous les paramètres pour une importation facile
ROBOCAR_CONFIG = {
    'port': '/dev/ttyACM1',
    'baudrate': 115200,
    'throttle_max': 0.1, # Puissance max moteur très réduite pour éviter l'OVP (0.0 à 1.0)
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
        self.max_throttle_change = 0.03  # Changement maximum par commande (3% - très conservateur)
        self.throttle_filter_alpha = 0.2  # Coefficient de lissage (0.2 = très lisse)
        self.emergency_triggered = False  # Flag pour détecter les situations d'urgence
        self.connection_lost = False  # Flag pour détecter les pertes de connexion

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
                # Arrêt immédiat pour éviter que l'alimentation coupe
                self._safe_vesc_command(self.vesc.set_duty_cycle, 0.0)
                self._safe_vesc_command(self.vesc.set_servo, self.steering_center_pos)
                time.sleep(0.05)  # Très courte pause
                
                # Tentative de fermeture propre avec timeout court
                try:
                    self.vesc.close()
                except:
                    pass  # Ignore les erreurs de fermeture si l'alimentation a coupé
                    
            except Exception as e:
                # Si erreur I/O, l'alimentation a probablement coupé
                if "Input/output error" in str(e) or "Errno 5" in str(e):
                    print("Alimentation coupée - connexion perdue")
                    self.connection_lost = True
                else:
                    print(f"Erreur lors de la déconnexion: {e}")
            finally:
                self.vesc = None
                self.current_throttle = 0.0
                self.previous_throttle = 0.0
                self.emergency_triggered = False
                print("Déconnecté.")

    def set_throttle(self, value):
        """Définit la puissance du moteur avec lissage et protection (-1.0 à 1.0)."""
        if not self.is_connected or self.connection_lost: 
            return

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
        
        # Utiliser la méthode sécurisée pour envoyer la commande
        self._safe_vesc_command(self.vesc.set_duty_cycle, duty_cycle)

    def set_steering(self, value):
        """Définit l'angle de direction (-1.0 à 1.0)."""
        if not self.is_connected or self.connection_lost: 
            return
            
        value = max(min(value, 1.0), -1.0) # borner la valeur
        if value < 0:
            servo_pos = self.steering_center_pos + value * (self.steering_center_pos - self.steering_left_limit)
        else:
            servo_pos = self.steering_center_pos + value * (self.steering_right_limit - self.steering_center_pos)
        
        # Utiliser la méthode sécurisée pour envoyer la commande
        self._safe_vesc_command(self.vesc.set_servo, servo_pos)

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
        if not self.is_connected: 
            return
            
        success = self._safe_vesc_command(self.vesc.set_duty_cycle, 0)
        if success:
            self.current_throttle = 0.0
        else:
            print("Erreur lors de l'arrêt d'urgence")

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
        if int(self.throttle_max_power * 10) < 5:
            self.throttle_max_power += 0.1
            vitesse = int(self.throttle_max_power * 10)
            self.play_sound(f'assets/Vitesse{vitesse}.wav')


    def decr_throttle_max(self):
        """Diminue la puissance maximale du moteur"""
        if int(self.throttle_max_power * 10) > 0:
            self.throttle_max_power -= 0.1
            vitesse = int(self.throttle_max_power * 10) + 1
            self.play_sound(f'assets/Vitesse{vitesse}.wav')

    def monitor_power_consumption(self):
        """Surveille la consommation pour prévenir l'OVP."""
        if not self.is_connected:
            return None
        
        try:
            # Essayer de lire les données du VESC
            current = self.vesc.get_measurements().input_current
            voltage = self.vesc.get_measurements().input_voltage
            
            # Calculer la puissance
            power = current * voltage
            
            # Alerte si proche des limites
            if current > 3.0:  # Ajustez selon votre alimentation
                print(f"⚠️  COURANT ÉLEVÉ: {current:.2f}A")
            if voltage > 12.5:  # Ajustez selon votre alimentation
                print(f"⚠️  TENSION ÉLEVÉE: {voltage:.2f}V")
                
            return {
                'current': current,
                'voltage': voltage,
                'power': power
            }
        except Exception as e:
            # Ignore silencieusement les erreurs de lecture
            return None

    def get_safe_throttle_increment(self):
        """Retourne un incrément de throttle sûr basé sur l'état actuel."""
        # Incrément encore plus conservateur si on détecte des problèmes
        base_increment = self.max_throttle_change
        
        if hasattr(self, 'connection_lost') and self.connection_lost:
            return 0.0  # Pas d'augmentation si connexion perdue
        
        # Réduire l'incrément si le throttle actuel est déjà élevé
        if abs(self.current_throttle) > 0.3:
            return base_increment * 0.5  # Moitié moins rapide
        elif abs(self.current_throttle) > 0.5:
            return base_increment * 0.25  # Encore plus lent
        
        return base_increment

    def play_sound(self, sound_file):
        """Joue un son spécifique."""
        if not self.is_connected: return
        try:
            subprocess.run(['./startMusic.sh', sound_file],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd='/home/epitechrobocar/robocar/Sound-Robocar')
        except Exception as e:
            print(f"Erreur lors de la lecture du son: {e}")

    def horn(self):
        """Active le klaxon."""
        try:
            self.play_sound('assets/circus_horn.wav')
        except Exception as e:
            print(f"Erreur lors de l'activation du klaxon: {e}")

    def _safe_vesc_command(self, command_func, *args, **kwargs):
        """Exécute une commande VESC de manière sécurisée avec gestion d'erreur.
        
        Args:
            command_func: La fonction VESC à appeler
            *args: Arguments positionnels pour la fonction
            **kwargs: Arguments nommés pour la fonction
            
        Returns:
            True si la commande a réussi, False sinon
        """
        if not self.is_connected or self.connection_lost:
            return False
            
        try:
            command_func(*args, **kwargs)
            return True
        except (ValueError, TypeError) as parse_error:
            print(f"Erreur de parsing VESC: {parse_error}")
            return False
        except Exception as e:
            # Si erreur I/O, marquer la connexion comme perdue
            if "Input/output error" in str(e) or "Errno 5" in str(e):
                print(f"\n❌ Connexion perdue (OVP alimentation?)")
                self.connection_lost = True
                self.emergency_triggered = True
            else:
                print(f"Erreur lors de l'envoi de la commande VESC: {e}")
            return False
