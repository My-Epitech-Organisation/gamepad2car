#!/usr/bin/env python3
"""
Test simple pour vérifier que les commandes arrivent bien au VESC.
Lance ce script sur le robot pour tester directement.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.robocar_base import Robocar, ROBOCAR_CONFIG
import time

def test_direct_control():
    """Test de contrôle direct sans réseau."""
    print("=== Test Contrôle Direct VESC ===\n")
    
    car = Robocar(**ROBOCAR_CONFIG)
    
    if not car.connect():
        print("❌ Impossible de se connecter au VESC")
        return
    
    print("✅ Connecté au VESC")
    
    try:
        # Test 1: Petit throttle avant
        print("\n1. Test throttle avant (0.2 pendant 2s)")
        car.set_throttle(0.2)
        time.sleep(2)
        car.set_throttle(0.0)
        time.sleep(1)
        
        # Test 2: Direction gauche
        print("2. Test direction gauche")
        car.set_steering(-0.5)
        time.sleep(1)
        car.set_steering(0.0)
        time.sleep(1)
        
        # Test 3: Direction droite
        print("3. Test direction droite")
        car.set_steering(0.5)
        time.sleep(1)
        car.set_steering(0.0)
        
        print("\n✅ Tests terminés")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        car.disconnect()

if __name__ == "__main__":
    test_direct_control()
