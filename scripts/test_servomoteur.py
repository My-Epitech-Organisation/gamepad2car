#!/usr/bin/env python3
"""
test_servomoteur.py

Pilote un servomoteur branché sur PB5 du VESC via UART en utilisant PyVESC.
"""

import time
import serial
from pyvesc import VESC

from pyvesc import encode
from pyvesc.VESC.messages.setters import SetServoPosition

# ── Configuration ────────────────────────────────────────────────────────────
PORT      = "/dev/ttyACM0"   # Change selon ton système (ex. COM3 sous Windows)
BAUDRATE  = 115200
TIMEOUT   = 0.1              # Secondes pour PySerial

# ── Fonction d’envoi de position servo ──────────────────────────────────────
def set_servo_normalized(ser, pos: float):
    """
    Envoie une position normalisée [0.0 → 1.0] au VESC.
    Le firmware mappe ensuite [0→1000] sur ta plage PWM 1000–2000 µs.
    """
    # Encode le message VESC et l’envoie
    packet = encode(SetServoPosition(pos))
    ser.write(packet)

# ── Routine principale ──────────────────────────────────────────────────────
def main():
    # 1) Ouverture du port série
    ser = serial.Serial(PORT, baudrate=BAUDRATE, timeout=TIMEOUT)
    time.sleep(0.1)  # Laisse le port se stabiliser

    try:
        # 2) Balayage de test : 0%, 25%, 50%, 75%, 100%, puis centrage
        for p in [0.0, 0.25, 0.5, 0.75, 1.0]:
            print(f"Servo → {p*100:.0f}%")
            set_servo_normalized(ser, p)
            time.sleep(0.5)

        print("Centrage à 50%")
        set_servo_normalized(ser, 0.5)

    finally:
        # 3) Fermeture propre
        ser.close()

if __name__ == "__main__":
    main()
