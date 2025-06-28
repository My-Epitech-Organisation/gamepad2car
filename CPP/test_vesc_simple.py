#!/usr/bin/env python3
"""
Script de test simple pour la classe Motor de vescLib.py
"""

import time
from vescLib import Motor

def test_basic_functions():
    print("=== Test des fonctions de base du VESC ===")
    
    # Création de l'objet Motor
    print("Connexion au VESC...")
    motor = Motor()
    
    try:
        # Test du servo (direction)
        print("\nTest de direction:")
        print("Centre...")
        motor.center_steering()
        time.sleep(1)
        
        print("Gauche (0.2)...")
        motor.set_steering(0.2)
        time.sleep(1)
        
        print("Droite (0.8)...")
        motor.set_steering(0.8)
        time.sleep(1)
        
        print("Centre...")
        motor.center_steering()
        time.sleep(1)
        
        # Test vitesse lente
        print("\nTest de vitesse faible:")
        print("Avance lente (20%)...")
        motor.set_speed(0.2)
        time.sleep(2)
        
        print("Arrêt...")
        motor.stop_motor()
        time.sleep(1)
        
        print("Recule lent (20%)...")
        motor.set_speed(-0.2)
        time.sleep(2)
        
        print("Arrêt avec frein...")
        motor.brake(0.5)
        time.sleep(1)
        
        # Récupérer le statut
        print("\nStatut du VESC:")
        status = motor.get_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
            
    except KeyboardInterrupt:
        print("\nTest interrompu par l'utilisateur")
    finally:
        # Arrêt propre
        print("\nArrêt et nettoyage...")
        motor.stop()
        
    print("Test terminé!")

if __name__ == "__main__":
    test_basic_functions()
