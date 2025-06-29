#!/usr/bin/env python3
"""
vescLib.py - API simplifiée pour contrôler un VESC (moteur et servo)
"""

import sys
import os
import time
import serial
import serial.tools.list_ports

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

# Variables globales pour l'API simplifiée
_vesc = None
_port = None

def init_vesc(port=None, max_duty_cycle=0.6):
    """
    Initialise la connexion au VESC
    
    Args:
        port: Port série (automatique si None)
        max_duty_cycle: Duty cycle maximum (0.0 à 1.0)
    
    Returns:
        True si succès, False sinon
    """
    global _vesc, _port
    
    try:
        if USE_SIMULATION:
            print("Mode simulation activé")
            _vesc = {"simulated": True, "port": port}
            return True
            
        # Import les modules PyVESC
        from PyVESC.pyvesc import encode
        from PyVESC.pyvesc.VESC.messages.setters import SetDutyCycle, SetServoPosition
            
        # Détection automatique du port
        if port is None:
            port = find_vesc_port()
            
        print(f"Connexion au VESC sur {port}...")
        _port = serial.Serial(port, 115200, timeout=0.1)
        
        # Stocker les fonctionnalités du VESC pour une utilisation ultérieure
        _vesc = {
            "port": _port,
            "max_duty_cycle": max_duty_cycle,
            "encode": encode,
            "SetDutyCycle": SetDutyCycle,
            "SetServoPosition": SetServoPosition
        }
        
        # Envoyer une commande d'arrêt initiale
        set_motor_speed(0)
        set_servo_position(0.5)  # Centre
        
        print("VESC initialisé avec succès")
        return True
    except Exception as e:
        print(f"Erreur lors de l'initialisation du VESC: {e}")
        return False

def set_motor_speed(speed):
    """
    Règle la vitesse du moteur
    
    Args:
        speed: Vitesse entre -1.0 (arrière) et 1.0 (avant)
    
    Returns:
        True si succès, False sinon
    """
    global _vesc
    
    if _vesc is None:
        print("VESC non initialisé")
        return False
        
    try:
        # Limiter entre -1 et 1
        speed = max(-1.0, min(1.0, speed))
        
        # Appliquer une courbe de puissance pour une meilleure réponse
        if abs(speed) < 0.05:
            # Zone morte
            speed_value = 0
        else:
            # Appliquer le max_duty_cycle
            if USE_SIMULATION:
                max_duty = 0.6
            else:
                max_duty = _vesc["max_duty_cycle"]
            
            speed_value = int(speed * max_duty * 100000)
        
        # Envoyer la commande
        if USE_SIMULATION:
            print(f"SIMULATION: SetDutyCycle({speed_value})")
        else:
            packet = _vesc["encode"](_vesc["SetDutyCycle"](speed_value))
            _vesc["port"].write(packet)
            
        print(f"Vitesse moteur: {speed:.2f} (duty cycle: {speed_value})")
        return True
    except Exception as e:
        print(f"Erreur en réglant la vitesse: {e}")
        return False

def set_servo_position(position):
    """
    Règle la position du servo (direction)
    
    Args:
        position: Position entre 0.0 (gauche) et 1.0 (droite), 0.5 centre
    
    Returns:
        True si succès, False sinon
    """
    global _vesc
    
    if _vesc is None:
        print("VESC non initialisé")
        return False
        
    try:
        # Limiter entre 0 et 1
        position = max(0.0, min(1.0, position))
        
        # Ajuster pour une meilleure amplitude
        # On va étendre la plage pour avoir plus d'angle
        adjusted_position = 0.05 + position * 0.9
        
        # Envoyer la commande
        if USE_SIMULATION:
            print(f"SIMULATION: SetServoPosition({adjusted_position:.4f})")
        else:
            packet = _vesc["encode"](_vesc["SetServoPosition"](adjusted_position))
            _vesc["port"].write(packet)
            
        print(f"Position servo: {position:.2f} (ajustée: {adjusted_position:.4f})")
        return True
    except Exception as e:
        print(f"Erreur en réglant la position du servo: {e}")
        return False

def center_steering():
    """
    Centre la direction (position 0.5)
    
    Returns:
        True si succès, False sinon
    """
    return set_servo_position(0.5)

def stop_motor():
    """
    Arrête le moteur
    
    Returns:
        True si succès, False sinon
    """
    return set_motor_speed(0.0)

def close_vesc():
    """
    Ferme proprement la connexion au VESC
    
    Returns:
        True si succès, False sinon
    """
    global _vesc, _port
    
    if _vesc is None:
        return True
        
    try:
        # Arrêt du moteur et centrage
        stop_motor()
        center_steering()
        time.sleep(0.1)
        
        # Fermeture du port série
        if not USE_SIMULATION and _port is not None:
            _port.close()
            
        _vesc = None
        _port = None
        print("Connexion VESC fermée")
        return True
    except Exception as e:
        print(f"Erreur lors de la fermeture du VESC: {e}")
        return False

# Fonction de test direct depuis Python
def test_vesc_movement():
    """
    Test simple du mouvement du servo et moteur
    """
    if not init_vesc():
        print("Échec de l'initialisation du VESC")
        return
    
    try:
        print("\n=== Test de direction ===")
        print("Centrer...")
        center_steering()
        time.sleep(1)
        
        print("Gauche (0.2)...")
        set_servo_position(0.2)
        time.sleep(1.5)
        
        print("Droite (0.8)...")
        set_servo_position(0.8)
        time.sleep(1.5)
        
        print("Centre (0.5)...")
        center_steering()
        time.sleep(1)
        
        print("\n=== Test du moteur ===")
        print("Démarrage 50%...")
        set_motor_speed(0.5)  # 50% en avant
        
        print("Running for 5 seconds...")
        time.sleep(5)
        
        print("Arrêt du moteur...")
        stop_motor()
        
        print("\nTest complété avec succès")
        
    finally:
        close_vesc()

# Exécution directe pour le test
if __name__ == "__main__":
    test_vesc_movement()
        