#!/usr/bin/env python3
"""
gamepad2car.py - Control a car using gamepad and PyVESC with video game-like controls
"""

import os
import sys
import time
import pygame
import serial
import pyvesc
import argparse
from pyvesc import SetDutyCycle, SetRPM, SetCurrent, SetCurrentBrake
from gamepad_config import GamepadConfig, Colors


class GamepadController:
    def __init__(self, config_only=False):
        self.running = True
        self.config_manager = GamepadConfig()
        self.joystick = None
        self.serial_conn = None

        # Control state variables
        self.throttle = 0.0
        self.steering = 0.0
        self.in_reverse_gear = False
        self.cruise_control_active = False
        self.cruise_control_speed = 0.0
        self.boost_active = False

        # Settings from configuration
        self.config = self.config_manager.config

        # Run calibration if requested
        if config_only:
            self.config_manager.run_calibration_menu()
            return

        # Initialize PyGame for controller input
        pygame.init()
        pygame.joystick.init()

        # Connect to the gamepad
        self.connect_gamepad()

        # Connect to the VESC
        self.connect_vesc()

    def connect_gamepad(self):
        """Connect to gamepad"""
        print(f"{Colors.YELLOW}Looking for gamepad...{Colors.RESET}")

        # Check if any joysticks/gamepads are connected
        if pygame.joystick.get_count() < 1:
            print(f"{Colors.RED}No gamepads found. Please connect a gamepad.{Colors.RESET}")
            return False

        # Initialize the first joystick
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        # Let the config manager know about the joystick
        self.config_manager.joystick = self.joystick

        # Display gamepad info
        name = self.joystick.get_name()
        print(f"{Colors.GREEN}Connected to: {name}{Colors.RESET}")

        return True

    def connect_vesc(self):
        """Connect to the VESC motor controller"""
        serial_port = self.config['performance'].get('serial_port', '/dev/ttyACM0')
        baud_rate = self.config['performance'].get('baud_rate', 115200)

        try:
            self.serial_conn = serial.Serial(serial_port, baud_rate, timeout=0.05)
            print(f"{Colors.GREEN}Connected to VESC at {serial_port}{Colors.RESET}")
            return True
        except serial.SerialException as e:
            print(f"{Colors.RED}Error connecting to VESC: {e}{Colors.RESET}")
            print(f"Make sure the VESC is connected to {serial_port} and you have permission to access it.")
            print("You may need to run: sudo chmod 666 " + serial_port)
            return False

    def send_to_vesc(self, throttle_value):
        """Send command to the VESC based on throttle input"""
        if self.serial_conn is None or not self.serial_conn.is_open:
            return

        try:
            # Get control mode and max values from config
            control_mode = self.config['performance']['control_mode']
            max_duty_cycle = self.config['performance']['max_duty_cycle']
            max_rpm = self.config['performance']['max_rpm']
            max_current = self.config['performance']['max_current']

            # Apply boost if active
            if self.boost_active:
                boost_multiplier = self.config['performance']['boost_multiplier']
                throttle_value *= boost_multiplier

            # Apply reverse gear if active
            if self.in_reverse_gear and throttle_value > 0:
                throttle_value = -throttle_value

            # Scale the throttle value based on the control mode
            if control_mode == 'duty_cycle':
                # Duty cycle ranges from -1.0 to 1.0 (converted to int for PyVESC)
                scaled_value = int(throttle_value * max_duty_cycle * 100000)
                msg = SetDutyCycle(scaled_value)
            elif control_mode == 'rpm':
                # RPM control
                scaled_value = int(throttle_value * max_rpm)
                msg = SetRPM(scaled_value)
            elif control_mode == 'current':
                # Current control
                scaled_value = throttle_value * max_current
                msg = SetCurrent(scaled_value)
            else:
                # Default to duty cycle
                scaled_value = int(throttle_value * max_duty_cycle * 100000)
                msg = SetDutyCycle(scaled_value)

            # Encode and send the message
            packet = pyvesc.encode(msg)
            self.serial_conn.write(packet)

        except Exception as e:
            print(f"{Colors.RED}Error sending command to VESC: {e}{Colors.RESET}")

    def handle_events(self):
        """Process events and controller inputs"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Handle controller disconnect/reconnect
            if event.type == pygame.JOYDEVICEREMOVED:
                print(f"{Colors.RED}Gamepad disconnected!{Colors.RESET}")
                self.joystick = None
                self.config_manager.joystick = None
                # Send zero throttle for safety
                self.throttle = 0.0
                self.send_to_vesc(0.0)

            if event.type == pygame.JOYDEVICEADDED:
                print(f"{Colors.GREEN}Gamepad connected!{Colors.RESET}")
                self.connect_gamepad()

            # Handle button presses for control toggles
            if event.type == pygame.JOYBUTTONDOWN:
                # Toggle reverse gear
                if self.config_manager.is_button_pressed("reverse"):
                    self.in_reverse_gear = not self.in_reverse_gear
                    print(f"{Colors.YELLOW}Reverse gear: {'ON' if self.in_reverse_gear else 'OFF'}{Colors.RESET}")
                    # Apply brakes when switching gears
                    self.send_emergency_brake()
                    time.sleep(0.1)

                # Toggle cruise control
                if self.config_manager.is_button_pressed("cruise_toggle"):
                    if not self.cruise_control_active:
                        # Activate cruise control at current speed
                        self.cruise_control_active = True
                        self.cruise_control_speed = self.throttle
                        print(f"{Colors.YELLOW}Cruise control activated at: {self.cruise_control_speed:.2f}{Colors.RESET}")
                    else:
                        # Deactivate cruise control
                        self.cruise_control_active = False
                        print(f"{Colors.YELLOW}Cruise control deactivated{Colors.RESET}")

    def send_emergency_brake(self):
        """Apply emergency brake"""
        print(f"{Colors.RED}EMERGENCY STOP!{Colors.RESET}")
        self.throttle = 0.0
        self.cruise_control_active = False

        # Apply brake and then zero throttle
        if self.serial_conn and self.serial_conn.is_open:
            try:
                max_current = self.config['performance']['max_current']
                msg = SetCurrentBrake(max_current)
                packet = pyvesc.encode(msg)
                self.serial_conn.write(packet)
                time.sleep(0.1)  # Short delay to ensure brake is applied
                self.send_to_vesc(0.0)
            except Exception as e:
                print(f"{Colors.RED}Error applying emergency brake: {e}{Colors.RESET}")

    def update_controls(self):
        """Read current gamepad state and update controls"""
        if self.joystick is None:
            return

        try:
            # Check for emergency stop
            if self.config_manager.is_button_pressed("emergency_stop"):
                self.send_emergency_brake()
                return

            # Check boost button
            self.boost_active = self.config_manager.is_button_pressed("boost")

            # Handle cruise control
            if self.cruise_control_active:
                # Use the current cruise control speed
                self.throttle = self.cruise_control_speed

                # Allow fine adjustment with throttle controls
                throttle_value = self.config_manager.get_control_value("throttle")
                if abs(throttle_value) > 0.5:  # Significant throttle input
                    # Adjust cruise control speed
                    increment = self.config['performance']['cruise_increment']
                    if throttle_value > 0:
                        self.cruise_control_speed += increment
                    else:
                        self.cruise_control_speed -= increment

                    # Clamp to reasonable range
                    self.cruise_control_speed = max(0.0, min(1.0, self.cruise_control_speed))
                    self.throttle = self.cruise_control_speed
                    print(f"{Colors.YELLOW}Cruise speed adjusted to: {self.cruise_control_speed:.2f}{Colors.RESET}")

                # Brake pedal or brake button cancels cruise control
                if self.config_manager.get_control_value("brake") > 0.2:
                    self.cruise_control_active = False
                    self.throttle = 0.0
                    print(f"{Colors.YELLOW}Cruise control deactivated by brake{Colors.RESET}")
            else:
                # Normal throttle control
                self.throttle = self.config_manager.get_control_value("throttle")

            # Steering control
            self.steering = self.config_manager.get_control_value("steering")

        except Exception as e:
            print(f"{Colors.RED}Error reading gamepad: {e}{Colors.RESET}")

    def display_controls(self):
        """Display current control state"""
        status = []
        status.append(f"Throttle: {self.throttle:+.2f}")
        status.append(f"Steering: {self.steering:+.2f}")

        if self.in_reverse_gear:
            status.append(f"{Colors.RED}REVERSE{Colors.RESET}")

        if self.boost_active:
            status.append(f"{Colors.YELLOW}BOOST{Colors.RESET}")

        if self.cruise_control_active:
            status.append(f"{Colors.GREEN}CRUISE:{self.cruise_control_speed:.2f}{Colors.RESET}")

        print(f"\r{' | '.join(status)}", end="")

    def run(self):
        """Main control loop"""
        print(f"\n{Colors.CYAN}=== Gamepad to Car Controller ==={Colors.RESET}")
        print("-" * 50)
        print(f"Control mode: {self.config['performance']['control_mode']}")
        print(f"{Colors.YELLOW}Controls:{Colors.RESET}")
        print("  Throttle/Brake: Mapped in configuration")
        print("  Steering: Mapped in configuration")
        print("  A Button: Boost (temporary speed increase)")
        print("  X Button: Toggle reverse gear")
        print("  B Button: Emergency stop")
        print("  Y Button: Toggle cruise control")
        print("  Ctrl+C: Quit")
        print(f"{Colors.YELLOW}Tip: Run with --config to calibrate your gamepad{Colors.RESET}")
        print("-" * 50)

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
                if current_time - last_display_time > 0.3:  # Update display every 0.3 seconds
                    self.display_controls()
                    last_display_time = current_time

                # Sleep to reduce CPU usage
                time.sleep(0.01)

        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Exiting...{Colors.RESET}")
        finally:
            # Cleanup
            if self.serial_conn and self.serial_conn.is_open:
                # Send zero command before closing
                self.send_to_vesc(0.0)
                self.serial_conn.close()

            pygame.quit()
            print(f"\n{Colors.GREEN}Controller stopped. Goodbye!{Colors.RESET}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Control a car with a gamepad using PyVESC')
    parser.add_argument('--config', action='store_true', help='Run gamepad configuration and calibration')
    args = parser.parse_args()

    controller = GamepadController(config_only=args.config)

    if not args.config:
        controller.run()