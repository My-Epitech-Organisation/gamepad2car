#!/usr/bin/env python3
"""
Wrapper Python pour la classe Motor de vescLib.py
Ce wrapper permet d'accéder aux fonctionnalités de la classe Motor depuis C++
"""

from vescLib import Motor
import sys
import time

# Instance globale du moteur
_motor = None

def initialize_motor(port=None, baudrate=115200, max_duty_cycle=0.6):
    """
    Initialise le moteur VESC
    
    Args:
        port: Port série du VESC (auto-détecté si None)
        baudrate: Débit en bauds
        max_duty_cycle: Duty cycle maximum (0.0 à 1.0) pour limiter la puissance (défaut: 0.6 = 60%)
        
    Returns:
        "OK" si l'initialisation est réussie, sinon un message d'erreur
    """
    global _motor
    try:
        _motor = Motor(port, baudrate, max_duty_cycle)
        return "OK"
    except Exception as e:
        return f"ERROR: {str(e)}"

def set_steering(position):
    """
    Règle la position du servo pour la direction
    
    Args:
        position: Position entre 0.0 (gauche) et 1.0 (droite), 0.5 est le centre
        
    Returns:
        "OK" si la commande est réussie, sinon un message d'erreur
    """
    global _motor
    if _motor is None:
        return "ERROR: Motor not initialized"
    try:
        _motor.set_steering(position)
        return "OK"
    except Exception as e:
        return f"ERROR: {str(e)}"

def set_speed(throttle):
    """
    Règle la vitesse du moteur
    
    Args:
        throttle: Valeur entre -1.0 (arrière max) et 1.0 (avant max), 0.0 est l'arrêt
        
    Returns:
        "OK" si la commande est réussie, sinon un message d'erreur
    """
    global _motor
    if _motor is None:
        return "ERROR: Motor not initialized"
    try:
        _motor.set_speed(throttle)
        return "OK"
    except Exception as e:
        return f"ERROR: {str(e)}"

def brake(power=1.0):
    """
    Applique un freinage actif
    
    Args:
        power: Puissance de freinage entre 0.0 (pas de frein) et 1.0 (frein max)
        
    Returns:
        "OK" si la commande est réussie, sinon un message d'erreur
    """
    global _motor
    if _motor is None:
        return "ERROR: Motor not initialized"
    try:
        _motor.brake(power)
        return "OK"
    except Exception as e:
        return f"ERROR: {str(e)}"

def stop_motor():
    """
    Arrête le moteur (duty cycle = 0)
    
    Returns:
        "OK" si la commande est réussie, sinon un message d'erreur
    """
    global _motor
    if _motor is None:
        return "ERROR: Motor not initialized"
    try:
        _motor.stop_motor()
        return "OK"
    except Exception as e:
        return f"ERROR: {str(e)}"

def center_steering():
    """
    Centre le servo (position 0.5)
    
    Returns:
        "OK" si la commande est réussie, sinon un message d'erreur
    """
    global _motor
    if _motor is None:
        return "ERROR: Motor not initialized"
    try:
        _motor.center_steering()
        return "OK"
    except Exception as e:
        return f"ERROR: {str(e)}"

def stop():
    """
    Arrête le moteur, centre le servo et ferme la connexion
    
    Returns:
        "OK" si la commande est réussie, sinon un message d'erreur
    """
    global _motor
    if _motor is None:
        return "ERROR: Motor not initialized"
    try:
        _motor.stop()
        _motor = None  # Réinitialiser la référence
        return "OK"
    except Exception as e:
        _motor = None  # Réinitialiser la référence même en cas d'erreur
        return f"ERROR: {str(e)}"

def get_status():
    """
    Récupère les informations actuelles du VESC
    
    Returns:
        Une chaîne formatée avec les informations ou un message d'erreur
    """
    global _motor
    if _motor is None:
        return "ERROR: Motor not initialized"
    try:
        status = _motor.get_status()
        result = "|".join([f"{k}:{v}" for k, v in status.items()])
        return result
    except Exception as e:
        return f"ERROR: {str(e)}"

# Fonction de test pour s'assurer que le module fonctionne
def test(msg):
    return f"Test successful: {msg}"

# Programme de test si exécuté directement
if __name__ == "__main__":
    print(initialize_motor())
    print(center_steering())
    time.sleep(1)
    print(set_steering(0.2))
    time.sleep(1)
    print(center_steering())
    time.sleep(1)
    print(set_speed(0.1))
    time.sleep(2)
    print(stop_motor())
    time.sleep(1)
    print(get_status())
    print(stop())
