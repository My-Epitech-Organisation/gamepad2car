#!/usr/bin/env python3
"""
gamepad2car.py - Control a car using gamepad and PyVESC with video game-like controls
"""

import os
import sys
import time

# Set environment variables to prevent D-Bus issues
# os.environ["SDL_AUDIODRIVER"] = "dummy"  # Commented out to enable sound
os.environ["SDL_DBUS_SCREENSAVER_INHIBIT"] = "0"

import pygame
import serial.tools.list_ports
from serial import Serial, SerialException
import pyvesc
import argparse
from pyvesc import encode
from pyvesc.VESC.messages.setters import SetDutyCycle, SetRPM, SetCurrent, SetCurrentBrake, SetServoPosition
from gamepad_config import GamepadConfig, Colors
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class GamepadController:
    def __init__(self, config_only=False):
        self.running = True
        self.config_manager = GamepadConfig()
        logging.debug("GamepadConfig initialized")
        self.joystick = None
        self.serial_conn = None

        # Control state variables
        self.throttle = 0.0
        self.steering = 0.0
        self.in_reverse_gear = False
        self.cruise_control_active = False
        self.cruise_control_speed = 0.0
        self.boost_active = False

        # Sound variables
        self.horn_sound = None

        # Settings from configuration
        self.config = self.config_manager.config

        # Run calibration if requested
        if config_only:
            self.config_manager.run_calibration_menu()
            return
        logging.debug("Calibration menu completed")

        # Initialize PyGame for controller input
        logging.debug("About to initialize pygame modules")
        # Initialize only necessary subsystems
        try:
            pygame.display.init()  # Pour l'affichage uniquement
            logging.debug("Display module initialized")
        except Exception as e:
            logging.error(f"Failed to initialize display: {e}")
            # Try with dummy display
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            try:
                pygame.display.init()
                logging.debug("Display module initialized with dummy driver")
            except Exception as e:
                logging.error(f"Failed even with dummy display: {e}")

        pygame.joystick.init() # Pour les manettes uniquement
        logging.debug("Joystick module initialized")

        # Initialize sound system
        self.init_sound()

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

    def init_sound(self):
        """Initialize pygame mixer and load sound files"""
        try:
            # Initialize mixer with appropriate settings for Jetson Nano
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            logging.debug("Pygame mixer initialized")
            
            # Load the circus horn sound
            horn_path = os.path.join(os.path.dirname(__file__), "assets", "circus_horn.wav")
            if os.path.exists(horn_path):
                self.horn_sound = pygame.mixer.Sound(horn_path)
                print(f"{Colors.GREEN}Horn sound loaded: {horn_path}{Colors.RESET}")
                logging.debug(f"Horn sound loaded from {horn_path}")
            else:
                print(f"{Colors.YELLOW}Warning: Horn sound file not found at {horn_path}{Colors.RESET}")
                logging.warning(f"Horn sound file not found at {horn_path}")
                
        except Exception as e:
            print(f"{Colors.RED}Error initializing sound: {e}{Colors.RESET}")
            logging.error(f"Error initializing sound: {e}")
            self.horn_sound = None

    def play_horn(self):
        """Play the horn sound effect"""
        if self.horn_sound:
            try:
                self.horn_sound.play()
                print(f"{Colors.CYAN}🔊 BEEP BEEP! 🔊{Colors.RESET}")
                logging.debug("Horn sound played")
            except Exception as e:
                print(f"{Colors.RED}Error playing horn sound: {e}{Colors.RESET}")
                logging.error(f"Error playing horn sound: {e}")
        else:
            print(f"{Colors.YELLOW}Horn sound not available{Colors.RESET}")

    def connect_vesc(self):
        """Connect to the VESC motor controller"""
        serial_port = self.config['performance'].get('serial_port', '/dev/ttyACM0')
        baud_rate = self.config['performance'].get('baud_rate', 115200)

        try:
            self.serial_conn = Serial(serial_port, baud_rate, timeout=0.05)
            print(f"{Colors.GREEN}Connected to VESC at {serial_port}{Colors.RESET}")
            return True
        except SerialException as e:
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
            packet = encode(msg)
            self.serial_conn.write(packet)

            # Envoyer la commande pour le servomoteur (contrôle de direction)
            if 'servo' in self.config and self.config['servo']['enabled']:
                # Obtenir les paramètres du servomoteur
                center_position = self.config['servo']['center_position']
                min_position = self.config['servo']['min_position']
                max_position = self.config['servo']['max_position']
                invert_direction = self.config['servo']['invert_direction']

                # Appliquer l'inversion de direction si nécessaire
                steering_value = self.steering
                if invert_direction:
                    steering_value = -steering_value

                # Convertir la valeur du joystick (-1.0 à 1.0) en position de servo (0.0 à 1.0)
                # Tenir compte de la position centrale et des limites
                if steering_value < 0:  # Tourner à gauche
                    servo_pos = center_position + (steering_value * (center_position - min_position))
                else:  # Tourner à droite ou tout droit
                    servo_pos = center_position + (steering_value * (max_position - center_position))

                # Limiter la position aux bornes min/max
                servo_pos = max(min_position, min(servo_pos, max_position))

                # Créer et envoyer le message de position de servo
                servo_msg = SetServoPosition(servo_pos)
                servo_packet = encode(servo_msg)
                self.serial_conn.write(servo_packet)

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

                # Toggle cruise control and play horn
                if self.config_manager.is_button_pressed("cruise_toggle"):
                    # Play horn sound when Y button is pressed
                    self.play_horn()
                    
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
                packet = encode(msg)
                self.serial_conn.write(packet)
                time.sleep(0.1)  # Short delay to ensure brake is applied
                self.send_to_vesc(0.0)

                # Center steering servo in emergency
                if 'servo' in self.config and self.config['servo']['enabled']:
                    center_position = self.config['servo']['center_position']
                    servo_msg = SetServoPosition(center_position)
                    servo_packet = encode(servo_msg)
                    self.serial_conn.write(servo_packet)

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
                throttle_input = self.config_manager.get_control_value("throttle")
                brake_input = self.config_manager.get_control_value("brake")
                net_throttle = throttle_input - brake_input

                if abs(net_throttle) > 0.3:  # Significant throttle/brake input
                    # Adjust cruise control speed
                    increment = self.config['performance']['cruise_increment']
                    if net_throttle > 0:
                        self.cruise_control_speed += increment
                    else:
                        self.cruise_control_speed -= increment

                    # Clamp to reasonable range
                    self.cruise_control_speed = max(0.0, min(1.0, self.cruise_control_speed))
                    self.throttle = self.cruise_control_speed
                    print(f"{Colors.YELLOW}Cruise speed adjusted to: {self.cruise_control_speed:.2f}{Colors.RESET}")

                # Brake pedal cancels cruise control
                if brake_input > 0.2:
                    self.cruise_control_active = False
                    self.throttle = 0.0
                    print(f"{Colors.YELLOW}Cruise control deactivated by brake{Colors.RESET}")
            else:
                # Normal throttle control with trigger-based input
                throttle_input = self.config_manager.get_control_value("throttle")
                brake_input = self.config_manager.get_control_value("brake")

                # Calculate net throttle: throttle - brake (racing-style controls)
                self.throttle = throttle_input - brake_input

                # Clamp the result to valid range
                self.throttle = max(-1.0, min(1.0, self.throttle))

            # Steering control
            self.steering = self.config_manager.get_control_value("steering")

        except Exception as e:
            print(f"{Colors.RED}Error reading gamepad: {e}{Colors.RESET}")

    def display_controls(self):
        """Display current control state"""
        # Get individual input values for display
        throttle_input = self.config_manager.get_control_value("throttle")
        brake_input = self.config_manager.get_control_value("brake")

        status = []
        status.append(f"RT: {throttle_input:.2f}")
        status.append(f"LT: {brake_input:.2f}")
        status.append(f"Net: {self.throttle:+.2f}")
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
        print("  RT (Right Trigger): Throttle/Acceleration")
        print("  LT (Left Trigger): Brake/Deceleration") 
        print("  Left Stick: Steering (contrôle du servomoteur sur pin PB5)")
        print("  A Button: Boost (temporary speed increase)")
        print("  X Button: Toggle reverse gear")
        print("  B Button: Emergency stop")
        print("  Y Button: Horn sound + Toggle cruise control")
        print("  Ctrl+C: Quit")

        # Afficher les informations du servomoteur si activé
        if 'servo' in self.config and self.config['servo']['enabled']:
            print(f"\n{Colors.YELLOW}Servo Control (Enabled):{Colors.RESET}")
            print(f"  Center: {self.config['servo']['center_position']}")
            print(f"  Range: {self.config['servo']['min_position']} (left) to {self.config['servo']['max_position']} (right)")
            print(f"  Direction: {'Inverted' if self.config['servo']['invert_direction'] else 'Normal'}")
        else:
            print(f"\n{Colors.RED}Servo Control: Disabled{Colors.RESET}")
            print("  Use --config option and select 'Configure Servo Settings' to enable steering control")

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

            # Cleanup pygame systems
            if pygame.mixer.get_init():
                pygame.mixer.quit()
            pygame.quit()
            print(f"\n{Colors.GREEN}Controller stopped. Goodbye!{Colors.RESET}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Control a car with a gamepad using PyVESC')
    parser.add_argument('--config', action='store_true', help='Run gamepad configuration and calibration')
    args = parser.parse_args()
    logging.debug("Command line arguments parsed")
    controller = GamepadController(config_only=args.config)
    logging.debug("GamepadController initialized")
    if not args.config:
        controller.run()
