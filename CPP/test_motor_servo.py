#!/usr/bin/env python3
"""
Script de test pour les mouvements du servo et du moteur
"""

import time
from vescLib import Motor
import sys

def test_servo_movement():
    """Test les mouvements du servo avec différentes amplitudes"""
    print("\n=== Test du servo (direction) ===")
    motor = Motor()
    
    try:
        # Test de mouvement complet de gauche à droite
        print("Test complet de gauche à droite:")
        
        print("Position extrême gauche (0.0)")
        motor.set_steering(0.0)
        time.sleep(1)
        
        print("Position 25% (0.25)")
        motor.set_steering(0.25)
        time.sleep(1)
        
        print("Position centre (0.5)")
        motor.set_steering(0.5)
        time.sleep(1)
        
        print("Position 75% (0.75)")
        motor.set_steering(0.75)
        time.sleep(1)
        
        print("Position extrême droite (1.0)")
        motor.set_steering(1.0)
        time.sleep(1)
        
        print("Retour au centre (0.5)")
        motor.set_steering(0.5)
        time.sleep(1)
        
        # Test de mouvement plus précis autour du centre
        print("\nTest de précision autour du centre:")
        positions = [0.45, 0.48, 0.5, 0.52, 0.55]
        
        for pos in positions:
            print(f"Position {pos:.2f}")
            motor.set_steering(pos)
            time.sleep(0.7)
        
        # Test de réactivité
        print("\nTest de réactivité gauche-droite rapide:")
        for _ in range(3):
            motor.set_steering(0.3)
            time.sleep(0.3)
            motor.set_steering(0.7)
            time.sleep(0.3)
        
        print("Retour au centre")
        motor.set_steering(0.5)
        
    finally:
        motor.center_steering()
        motor.stop_motor()
        print("Test servo terminé")
        return motor  # Retourner l'objet motor pour le test suivant

def test_motor_movement(motor=None):
    """Test les mouvements du moteur avec différentes vitesses"""
    print("\n=== Test du moteur (accélération) ===")
    
    if motor is None:
        motor = Motor()
    
    try:
        # Test de vitesse progressive avant
        print("Test d'accélération progressive avant:")
        speeds = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        for speed in speeds:
            print(f"Vitesse avant: {speed:.1f}")
            motor.set_speed(speed)
            time.sleep(1)
        
        print("Arrêt")
        motor.stop_motor()
        time.sleep(1)
        
        # Test de vitesse progressive arrière si supporté
        print("\nTest d'accélération progressive arrière:")
        speeds = [-0.1, -0.2, -0.3]
        
        for speed in speeds:
            print(f"Vitesse arrière: {speed:.1f}")
            motor.set_speed(speed)
            time.sleep(1)
        
        print("Arrêt avec freinage")
        motor.brake(0.5)
        time.sleep(1)
        
    finally:
        motor.stop_motor()
        print("Test moteur terminé")
        motor.stop()

if __name__ == "__main__":
    print("=== DÉMARRAGE DES TESTS DE MOUVEMENT ===")
    
    if len(sys.argv) > 1 and sys.argv[1] == "servo":
        # Test du servo uniquement
        test_servo_movement()
    elif len(sys.argv) > 1 and sys.argv[1] == "motor":
        # Test du moteur uniquement
        test_motor_movement()
    else:
        # Test complet
        print("Test complet (servo puis moteur)")
        motor = test_servo_movement()
        test_motor_movement(motor)
    
    print("\n=== TESTS TERMINÉS ===")
