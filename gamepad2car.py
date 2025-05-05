#!/usr/bin/env python3
"""
gamepad2car.py - Control a car using Logitech F710 gamepad and PyVESC
"""

import os
import sys
import time
import pygame
import serial
import pyvesc
from pyvesc import SetDutyCycle, SetRPM, SetCurrent, SetCurrentBrake

# Configuration
SERIAL_PORT = '/dev/ttyACM0'  # Update this to match your VESC port
BAUD_RATE = 115200
MAX_DUTY_CYCLE = 0.3          # Maximum duty cycle (0.0 to 1.0)
MAX_RPM = 5000                # Maximum motor RPM
MAX_CURRENT = 10              # Maximum motor current (Amps)
CONTROL_MODE = 'duty_cycle'   # Options: 'duty_cycle', 'rpm', 'current'
DEADZONE = 0.05               # Joystick deadzone


class GamepadController:
    def __init__(self):
        self.running = True
        self.joystick = None
        self.serial_conn = None
        self.throttle = 0.0
        self.steering = 0.0

        # Initialize PyGame for controller input
        pygame.init()
        pygame.joystick.init()

        # Connect to the gamepad
        self.connect_gamepad()

        # Connect to the VESC
        self.connect_vesc()

    def connect_gamepad(self):
        """Connect to F710 gamepad"""
        print("Looking for F710 gamepad...")

        # Check if any joysticks/gamepads are connected
        if pygame.joystick.get_count() < 1:
            print("No gamepads found. Please connect F710 gamepad.")
            return False

        # Initialize the first joystick
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        # Check if it's an F710 (or compatible) gamepad
        name = self.joystick.get_name()
        print(f"Connected to: {name}")
        if 'f710' not in name.lower() and 'logitech' not in name.lower():
            print("Warning: This may not be an F710 gamepad. Controls might not work as expected.")

        return True

    def connect_vesc(self):
        """Connect to the VESC motor controller"""
        try:
            self.serial_conn = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.05)
            print(f"Connected to VESC at {SERIAL_PORT}")
            return True
        except serial.SerialException as e:
            print(f"Error connecting to VESC: {e}")
            print(f"Make sure the VESC is connected to {SERIAL_PORT} and you have permission to access it.")
            print("You may need to run: sudo chmod 666 " + SERIAL_PORT)
            return False

    def send_to_vesc(self, throttle_value):
        """Send command to the VESC based on throttle input"""
        if self.serial_conn is None or not self.serial_conn.is_open:
            return

        try:
            # Scale the throttle value based on the control mode
            if CONTROL_MODE == 'duty_cycle':
                # Duty cycle ranges from -1.0 to 1.0 (converted to int for PyVESC)
                scaled_value = int(throttle_value * MAX_DUTY_CYCLE * 100000)
                msg = SetDutyCycle(scaled_value)
            elif CONTROL_MODE == 'rpm':
                # RPM control
                scaled_value = int(throttle_value * MAX_RPM)
                msg = SetRPM(scaled_value)
            elif CONTROL_MODE == 'current':
                # Current control
                scaled_value = throttle_value * MAX_CURRENT
                msg = SetCurrent(scaled_value)
            else:
                # Default to duty cycle
                scaled_value = int(throttle_value * MAX_DUTY_CYCLE * 100000)
                msg = SetDutyCycle(scaled_value)

            # Encode and send the message
            packet = pyvesc.encode(msg)
            self.serial_conn.write(packet)

        except Exception as e:
            print(f"Error sending command to VESC: {e}")

    def apply_deadzone(self, value):
        """Apply deadzone to avoid small unintended movements"""
        if abs(value) < DEADZONE:
            return 0.0
        return value

    def handle_events(self):
        """Process events and controller inputs"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Handle controller disconnect/reconnect
            if event.type == pygame.JOYDEVICEREMOVED:
                print("Gamepad disconnected!")
                self.joystick = None
                # Send zero throttle for safety
                self.throttle = 0.0
                self.send_to_vesc(0.0)

            if event.type == pygame.JOYDEVICEADDED:
                print("Gamepad connected!")
                self.connect_gamepad()

    def update_controls(self):
        """Read current gamepad state and update controls"""
        if self.joystick is None:
            return

        try:
            # Right stick vertical axis (inverted) for throttle
            # Different controllers may use different axis mappings
            throttle_axis = 3  # Typically axis 3 on F710
            raw_throttle = -self.joystick.get_axis(throttle_axis)  # Invert so up is positive
            self.throttle = self.apply_deadzone(raw_throttle)

            # Left stick horizontal for steering
            steering_axis = 0  # Typically axis 0 on F710
            raw_steering = self.joystick.get_axis(steering_axis)
            self.steering = self.apply_deadzone(raw_steering)

            # Check for emergency stop (B button)
            if self.joystick.get_button(1):  # B button is typically 1 on F710
                print("EMERGENCY STOP!")
                self.throttle = 0.0
                # Apply brake
                if CONTROL_MODE == 'duty_cycle':
                    msg = SetCurrentBrake(MAX_CURRENT)
                    packet = pyvesc.encode(msg)
                    self.serial_conn.write(packet)
                    time.sleep(0.1)  # Short delay to ensure brake is applied
                self.send_to_vesc(0.0)

        except Exception as e:
            print(f"Error reading gamepad: {e}")

    def run(self):
        """Main control loop"""
        print("F710 Gamepad to Car Controller")
        print("-" * 40)
        print(f"Control mode: {CONTROL_MODE}")
        print("Controls:")
        print("  Right stick up/down: Throttle/Reverse")
        print("  Left stick left/right: Steering (not implemented in this version)")
        print("  B button: Emergency stop")
        print("  Ctrl+C: Quit")
        print("-" * 40)

        try:
            last_display_time = 0

            while self.running:
                # Handle pygame events (including controller connect/disconnect)
                self.handle_events()

                # Update control values from gamepad
                self.update_controls()

                # Send commands to VESC
                self.send_to_vesc(self.throttle)

                # Display current values (but not too frequently)
                current_time = time.time()
                if current_time - last_display_time > 0.5:  # Update display every 0.5 seconds
                    print(f"\rThrottle: {self.throttle:+.2f} | Steering: {self.steering:+.2f}", end="")
                    last_display_time = current_time

                # Sleep to reduce CPU usage
                time.sleep(0.01)

        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            # Cleanup
            if self.serial_conn and self.serial_conn.is_open:
                # Send zero command before closing
                self.send_to_vesc(0.0)
                self.serial_conn.close()

            pygame.quit()
            print("\nController stopped. Goodbye!")


if __name__ == "__main__":
    controller = GamepadController()
    controller.run()