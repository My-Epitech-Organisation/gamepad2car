#!/usr/bin/env python3
"""
Script de test pour vérifier les chemins d'importation Python
"""

import sys
import os

def print_system_info():
    print("=== Information Système ===")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    print("\n=== Python Path ===")
    for path in sys.path:
        print(f"- {path}")

def test_imports():
    print("\n=== Test d'importation ===")
    try:
        print("Tentative d'importation de PyVESC.pyvesc...")
        from PyVESC.pyvesc import VESC
        print("  Succès!")
    except ImportError as e:
        print(f"  Échec: {e}")
    
    try:
        print("Tentative d'importation de pyvesc...")
        import pyvesc
        print("  Succès!")
    except ImportError as e:
        print(f"  Échec: {e}")
    
    try:
        print("Tentative d'importation de vescLib...")
        from vescLib import Motor
        print("  Succès!")
        print("  Création d'une instance Motor...")
        motor = Motor()
        print("  Instance Motor créée avec succès!")
    except Exception as e:
        print(f"  Échec: {e}")
    
    try:
        print("Tentative d'importation de vesc_wrapper...")
        import vesc_wrapper
        print("  Succès!")
        print("  Test fonction initialize_motor...")
        result = vesc_wrapper.initialize_motor()
        print(f"  Résultat: {result}")
    except Exception as e:
        print(f"  Échec: {e}")

if __name__ == "__main__":
    print_system_info()
    test_imports()
