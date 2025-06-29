#!/usr/bin/env python3
"""
Script spécial pour tester et diagnostiquer le problème de servo direction
"""

import time
import sys
import os
import traceback

# Ajouter les chemins pour l'importation
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
if os.path.exists(os.path.join(current_dir, 'PyVESC')):
    sys.path.append(os.path.join(current_dir, 'PyVESC'))

# Tenter d'utiliser directement le module VESC sans passer par notre classe Motor
try:
    print("=== TEST DIRECT DU SERVO AVEC PyVESC ===")
    from PyVESC.pyvesc.VESC.VESC import VESC
    
    # Trouver le port série
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    print("Ports série disponibles:")
    for port in ports:
        print(f"  {port.device} - {port.description}")
    
    # Tester avec les ports disponibles ou utiliser le port par défaut
    if ports:
        port = ports[0].device  # Utiliser le premier port détecté
    else:
        port = '/dev/ttyACM0'  # Port par défaut
        
    print(f"\nUtilisation du port {port}")
    
    # Créer une connexion VESC directe
    vesc = VESC(port)
    print("Connexion VESC établie!")
    
    # Tester le servo avec différentes positions et pauses pour voir les mouvements
    print("\n=== TESTS SERVO AVEC DIFFÉRENTES MÉTHODES ===")
    
    # Arrêter le moteur d'abord
    print("Arrêt du moteur principal...")
    vesc.set_duty_cycle(0)
    time.sleep(1)
    
    # Méthode 1: Test standard avec set_servo
    print("\nTest 1: Méthode standard set_servo")
    print("Position centre (0.5)")
    vesc.set_servo(0.5)
    time.sleep(2)
    
    print("Position gauche (0.0)")
    vesc.set_servo(0.0)
    time.sleep(2)
    
    print("Position droite (1.0)")
    vesc.set_servo(1.0)
    time.sleep(2)
    
    print("Retour au centre (0.5)")
    vesc.set_servo(0.5)
    time.sleep(2)
    
    # Nettoyer
    vesc.serial_port.close()
    print("Connexion fermée proprement")
    
except Exception as e:
    print(f"ERREUR: {e}")
    traceback.print_exc()
    
# Tentative avec d'autres valeurs de servo via notre classe Motor
try:
    print("\n\n=== TEST AVEC DIFFÉRENTES PLAGES DE VALEURS ===")
    from vescLib import Motor
    
    # Créer l'objet Motor
    motor = Motor()
    print("Objet Motor créé")
    
    # Test avec différentes valeurs min/max
    print("\nTest avec des valeurs extrêmes:")
    
    # Valeurs originales selon le VESC Tool typique
    print("Valeurs VESC typiques:")
    print("Position gauche (0.0) - correspond à ~1ms")
    motor.set_steering(0.0)
    time.sleep(2)
    
    print("Position centre (0.5) - correspond à ~1.5ms")
    motor.set_steering(0.5)
    time.sleep(2)
    
    print("Position droite (1.0) - correspond à ~2ms")
    motor.set_steering(1.0)
    time.sleep(2)
    
    # Tester plus large pour voir si le servo répond
    # Attention: ces valeurs peuvent être hors spécifications pour certains servos
    print("\nTest avec plage étendue de valeurs:")
    for pos in [0.3, 0.4, 0.5, 0.6, 0.7]:
        print(f"Position {pos:.1f}")
        motor.set_steering(pos)
        time.sleep(1.5)
    
    print("\nTest terminé - arrêt propre")
    motor.stop()
    
except Exception as e:
    print(f"ERREUR: {e}")
    traceback.print_exc()

# Suggestions et diagnostics
print("\n=== SUGGESTIONS DE DÉPANNAGE ===")
print("Si le servo ne bouge toujours pas:")
print("1. Vérifiez les connexions physiques (câbles) entre VESC et servo")
print("2. Vérifiez l'alimentation du servo (suffisamment de courant?)")
print("3. Vérifiez que le VESC est configuré pour le contrôle PPM sur le bon port")
print("4. Essayez de configurer le VESC avec VESC Tool:")
print("   - Connectez-vous via USB")
print("   - Dans 'Input', configurez PPM comme contrôle")
print("   - Dans 'PPM Settings', configurez la plage du servo")
print("5. Testez le servo indépendamment avec un Arduino ou un testeur de servo")
print("6. Si tout échoue, essayez un autre servo pour éliminer un problème matériel")
