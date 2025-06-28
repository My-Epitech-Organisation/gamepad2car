import sys
import os
# Ajouter le chemin absolu des modules PyVESC si nécessaire
current_dir = os.path.dirname(os.path.abspath(__file__))
pyvesc_path = os.path.join(current_dir, 'PyVESC')
if pyvesc_path not in sys.path:
    sys.path.append(pyvesc_path)

try:
    from PyVESC.pyvesc import *
    from PyVESC.pyvesc.VESC.VESC import VESC
except ImportError:
    # Essayer une importation relative si la première échoue
    try:
        from pyvesc import *
        from pyvesc.VESC.VESC import VESC
    except ImportError:
        print("Erreur d'importation PyVESC. Chemins de recherche Python:", sys.path)
        print("Mode simulation activé (pas de connexion VESC réelle)")
        
        # Créer une classe VESC de simulation
        class VESC:
            def __init__(self, port=None, baudrate=None):
                self.port = port
                self.serial_port = type('obj', (object,), {'close': lambda: None})
                print(f"VESC simulé créé (port={port}, baudrate={baudrate})")
                
            def set_duty_cycle(self, duty_cycle):
                print(f"SIMULATION: set_duty_cycle({duty_cycle})")
                
            def set_servo(self, position):
                print(f"SIMULATION: set_servo({position})")
                
            def set_current(self, current):
                print(f"SIMULATION: set_current({current})")
                
            def get_measurements(self):
                return type('obj', (object,), {
                    'rpm': 0,
                    'duty_now': 0,
                    'v_in': 12.0,
                    'current_motor': 0,
                    'current_in': 0
                })

import time


class Motor:
    """
    Classe pour contrôler un moteur et un servo via VESC
    Usage simple:
    
    motor = Motor()
    motor.set_speed(0.5)    # 50% de vitesse en avant
    motor.set_steering(0.7) # 70% à droite (0.5 = centre)
    motor.brake(0.8)        # Frein à 80% de puissance
    motor.stop()            # Arrêt complet
    """
    
    def __init__(self, port='/dev/ttyACM0', baudrate=115200, max_duty_cycle=0.3):
        """
        Initialise la connexion au VESC
        
        Args:
            port: Port série du VESC (défaut: /dev/ttyACM0)
            baudrate: Débit en bauds (défaut: 115200)
            max_duty_cycle: Duty cycle maximum (0.0 à 1.0) pour limiter la puissance
        """
        try:
            self._vesc = VESC(port, baudrate=baudrate)
            self._max_duty_cycle = max_duty_cycle
            self._is_connected = True
            self._center_pos = 0.5  # Position centrale du servo
            print(f"Connexion VESC établie sur {port}")
            # Initialisation - arrêt moteur et centrage servo
            self.stop_motor()
            self.center_steering()
        except Exception as e:
            self._is_connected = False
            print(f"Erreur lors de la connexion au VESC: {e}")
    
    def set_steering(self, position) -> None:
        """
        Tourne le servo à une position spécifique
        
        Args:
            position: Position du servo entre 0.0 (gauche) et 1.0 (droite), 0.5 est le centre
        """
        if not self._is_connected:
            return
            
        # Limiter la valeur entre 0 et 1
        position = max(0.0, min(position, 1.0))
        
        try:
            self._vesc.set_servo(position)
            print(f"Servo positionné à {position:.2f}")
        except Exception as e:
            print(f"Erreur de contrôle du servo: {e}")
    
    def set_speed(self, throttle) -> None:
        """
        Règle la vitesse du moteur
        
        Args:
            throttle: Valeur entre -1.0 (arrière max) et 1.0 (avant max), 0.0 est l'arrêt
        """
        if not self._is_connected:
            return
            
        # Limiter la valeur entre -1 et 1
        throttle = max(-1.0, min(throttle, 1.0))
        
        # Convertir en valeur de duty cycle avec limitation de puissance
        duty_cycle = throttle * self._max_duty_cycle * 100000  # Conversion pour VESC (-100000 à 100000)
        
        try:
            self._vesc.set_duty_cycle(int(duty_cycle))
            print(f"Vitesse réglée à {throttle:.2f} (duty cycle: {duty_cycle})")
        except Exception as e:
            print(f"Erreur de contrôle du moteur: {e}")
    
    def brake(self, power=1.0) -> None:
        """
        Applique un freinage actif
        
        Args:
            power: Puissance de freinage entre 0.0 (pas de frein) et 1.0 (frein max)
        """
        if not self._is_connected:
            return
        
        # Limiter entre 0 et 1
        power = max(0.0, min(power, 1.0))
        
        try:
            current = 10 * power  # Ajuster selon les besoins, max ~10A pour freinage
            self._vesc.set_current(0)  # Pour éviter une transition brusque
            time.sleep(0.01)
            self._vesc.set_duty_cycle(0)  # Duty cycle à 0
            print(f"Frein appliqué à {power:.2f}")
        except Exception as e:
            print(f"Erreur lors du freinage: {e}")
    
    def stop_motor(self) -> None:
        """Arrête le moteur (duty cycle = 0)"""
        if not self._is_connected:
            return
        try:
            self._vesc.set_duty_cycle(0)
            print("Moteur arrêté")
        except Exception as e:
            print(f"Erreur lors de l'arrêt du moteur: {e}")
    
    def center_steering(self) -> None:
        """Centre le servo (position 0.5)"""
        self.set_steering(self._center_pos)
    
    def stop(self) -> None:
        """Arrête le moteur, centre le servo et ferme la connexion"""
        if not self._is_connected:
            return
        try:
            self.stop_motor()
            self.center_steering()
            time.sleep(0.1)  # Attendre que les commandes soient traitées
            self._vesc.serial_port.close()  # Fermer proprement la connexion série
            self._is_connected = False
            print("Connexion VESC fermée")
        except Exception as e:
            print(f"Erreur lors de la fermeture: {e}")
    
    def get_status(self) -> dict:
        """
        Récupère les informations actuelles du VESC
        
        Returns:
            Un dictionnaire avec les valeurs actuelles (vitesse, tension, courant)
        """
        if not self._is_connected:
            return {"error": "Non connecté"}
            
        try:
            measurements = self._vesc.get_measurements()
            return {
                "rpm": measurements.rpm,
                "duty_cycle": measurements.duty_now,
                "voltage": measurements.v_in,
                "motor_current": measurements.current_motor,
                "input_current": measurements.current_in
            }
        except Exception as e:
            print(f"Erreur lors de la récupération des mesures: {e}")
            return {"error": str(e)}
        