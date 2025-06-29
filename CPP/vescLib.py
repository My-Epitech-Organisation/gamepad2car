import sys
import os
# Ajouter le chemin absolu des modules PyVESC si nécessaire
current_dir = os.path.dirname(os.path.abspath(__file__))
pyvesc_path = os.path.join(current_dir, 'PyVESC')
if pyvesc_path not in sys.path:
    sys.path.append(pyvesc_path)
pyvesc_path = os.path.join(current_dir, 'PyVESC/pyvesc')
if pyvesc_path not in sys.path:
    sys.path.append(pyvesc_path)

# Variable pour activer/désactiver la simulation
USE_SIMULATION = False

def find_vesc_port():
    """
    Recherche automatiquement le port série du VESC
    
    Returns:
        Le chemin du port série du VESC ou None s'il n'est pas trouvé
    """
    try:
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        
        # Chercher d'abord les ports contenant "VESC" dans la description
        for port in ports:
            if "VESC" in port.description:
                return port.device
                
        # Ensuite chercher les ports contenant "ChibiOS" (firmware STM32 du VESC)
        for port in ports:
            if "ChibiOS" in port.description:
                return port.device
        
        # Si toujours pas trouvé, essayer /dev/ttyACM0 ou /dev/ttyACM1 s'ils existent
        for port in ports:
            if "ttyACM" in port.device:
                return port.device
                
        # Rien trouvé
        if ports:
            # Retourner le premier port disponible
            return ports[0].device
        return '/dev/ttyACM0'  # Port par défaut
    except:
        return '/dev/ttyACM0'  # En cas d'erreur, utiliser le port par défaut

try:
    if not USE_SIMULATION:
        from PyVESC.pyvesc import *
        from PyVESC.pyvesc.VESC.VESC import VESC
        print("Mode VESC réel activé")
    else:
        raise ImportError("Mode simulation forcé")
except ImportError as e:
    print(f"Utilisation du mode simulation VESC : {str(e)}")
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
    
    def __init__(self, port=None, baudrate=115200, max_duty_cycle=0.6):
        """
        Initialise la connexion au VESC
        
        Args:
            port: Port série du VESC (auto-détecté si None)
            baudrate: Débit en bauds (défaut: 115200)
            max_duty_cycle: Duty cycle maximum (0.0 à 1.0) pour limiter la puissance (défaut: 0.6 = 60%)
        """
        # Définir d'abord les attributs essentiels
        self._center_pos = 0.5
        self._max_duty_cycle = max_duty_cycle
        self._is_connected = False
        self._servo_initialized = False
        
        # Auto-détection du port si non spécifié
        if port is None:
            port = find_vesc_port()
            print(f"Port VESC auto-détecté: {port}")
        
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
        
        # Augmenter l'amplitude du mouvement en élargissant la plage
        # Mapper la position de [0,1] vers une plage plus large [0.05, 0.95] pour le servo
        # Cela donne une plus grande amplitude de mouvement
        adjusted_position = 0.05 + position * 0.9
        
        try:
            # Force une initialisation du servo avant de définir la position réelle
            # Cela peut aider si le servo était en mode sommeil ou nécessite un réveil
            if not hasattr(self, '_servo_initialized'):
                print("Initialisation du servo...")
                # Envoyer une séquence d'initialisation
                self._vesc.set_servo(0.5)  # Centre
                time.sleep(0.1)
                self._vesc.set_servo(0.6)  # Légèrement à droite
                time.sleep(0.1)
                self._vesc.set_servo(0.5)  # Retour au centre
                time.sleep(0.1)
                self._servo_initialized = True
            
            # Maintenant définir la position réelle
            self._vesc.set_servo(adjusted_position)
            print(f"Servo positionné à {position:.2f} (ajusté à {adjusted_position:.2f})")
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
        
        # Ajouter une zone morte et une courbe de réponse non linéaire
        if abs(throttle) < 0.05:
            # Zone morte pour éviter les micro-mouvements
            duty_cycle = 0
        else:
            # Appliquer un mapping exponentiel pour une meilleure réponse de l'accélération
            # Conserver le signe de throttle mais exponentiel sa magnitude
            # y = sign(x) * x^2 donne une courbe plus douce au début et plus agressive en fin de course
            sign = 1 if throttle >= 0 else -1
            throttle_adjusted = sign * (abs(throttle) ** 1.5)  # Exposant 1.5 pour une courbe plus agressive
            
            # Convertir en valeur de duty cycle avec limitation de puissance
            duty_cycle = throttle_adjusted * self._max_duty_cycle * 100000  # Conversion pour VESC (-100000 à 100000)
        
        try:
            self._vesc.set_duty_cycle(int(duty_cycle))
            print(f"Vitesse réglée à {throttle:.2f} (ajusté à {int(duty_cycle)}, max_duty: {self._max_duty_cycle})")
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
            # Arrêter le moteur et centrer le servo
            self.stop_motor()
            self.center_steering()
            time.sleep(0.1)  # Attendre que les commandes soient traitées
            
            # Arrêter le thread de heartbeat si présent (attribut spécifique au VESC)
            # Pour éviter l'erreur "PortNotOpenError" après la fermeture
            if hasattr(self._vesc, '_heartbeat_thread') and self._vesc._heartbeat_thread is not None:
                try:
                    # Arrêter proprement le thread s'il existe un moyen de le faire
                    if hasattr(self._vesc, '_heartbeat_stop') and isinstance(self._vesc._heartbeat_stop, bool):
                        self._vesc._heartbeat_stop = True
                        time.sleep(0.1)  # Laisser le temps au thread de se terminer
                except:
                    pass  # Ignorer les erreurs lors de l'arrêt du thread
            
            # Fermer le port série
            if hasattr(self._vesc, 'serial_port') and self._vesc.serial_port is not None:
                self._vesc.serial_port.close()
                
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
            status = {}
            
            # Tester la présence de chaque attribut avant de l'utiliser
            if hasattr(measurements, 'rpm'):
                status["rpm"] = measurements.rpm
            if hasattr(measurements, 'duty_now'):
                status["duty_cycle"] = measurements.duty_now
            elif hasattr(measurements, 'duty_cycle'):  # Nom alternatif possible
                status["duty_cycle"] = measurements.duty_cycle
            else:
                status["duty_cycle"] = 0  # Valeur par défaut
                
            if hasattr(measurements, 'v_in'):
                status["voltage"] = measurements.v_in
            elif hasattr(measurements, 'voltage_in'):  # Nom alternatif possible
                status["voltage"] = measurements.voltage_in
                
            if hasattr(measurements, 'current_motor'):
                status["motor_current"] = measurements.current_motor
            if hasattr(measurements, 'current_in'):
                status["input_current"] = measurements.current_in
                
            return status
        except Exception as e:
            print(f"Erreur lors de la récupération des mesures: {e}")
            return {"error": str(e)}
        