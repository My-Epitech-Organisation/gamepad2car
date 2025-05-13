#!/usr/bin/env python3
"""
gamepad_config.py - Gamepad configuration and calibration for gamepad2car

This module provides:
1. Gamepad calibration interface
2. Control mapping customization
3. Configuration saving/loading
4. User-friendly key handling
"""

import os
import json
# Set environment variables to prevent D-Bus issues BEFORE importing pygame
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["SDL_DBUS_SCREENSAVER_INHIBIT"] = "0"
os.environ["SDL_VIDEODRIVER"] = "dummy"  # Prevent display initialization issues

import pygame
import time
import sys

# Default configuration
DEFAULT_CONFIG = {
    # Control mappings
    "controls": {
        "throttle_axis": 3,       # Right stick vertical (F710)
        "brake_axis": 2,          # Left trigger (F710)
        "steering_axis": 0,       # Left stick horizontal (F710)
        "emergency_stop_btn": 1,  # B button (F710)
        "boost_btn": 0,           # A button (F710)
        "reverse_btn": 2,         # X button (F710)
        "cruise_toggle_btn": 3,   # Y button (F710)
    },
    # Calibration settings
    "calibration": {
        "throttle_deadzone": 0.05,
        "steering_deadzone": 0.05,
        "throttle_min": -1.0,
        "throttle_max": 1.0,
        "steering_min": -1.0,
        "steering_max": 1.0,
        "invert_throttle": True,   # Invert throttle so pushing up is positive
        "invert_steering": False,
    },
    # Performance settings
    "performance": {
        "max_duty_cycle": 0.3,    # Maximum duty cycle (0.0 to 1.0)
        "max_rpm": 5000,          # Maximum motor RPM
        "max_current": 10,        # Maximum motor current (Amps)
        "control_mode": "duty_cycle",  # Options: 'duty_cycle', 'rpm', 'current'
        "boost_multiplier": 1.5,  # Multiplier when boost button is pressed
        "cruise_increment": 0.05, # Increment for cruise control
    },
    # Servo settings
    "servo": {
        "enabled": True,          # Active le contrôle du servomoteur
        "center_position": 0.5,   # Position centrale (tout droit)
        "min_position": 0.0,      # Position minimale (complètement à gauche)
        "max_position": 1.0,      # Position maximale (complètement à droite)
        "invert_direction": False, # Inverser la direction du servo
    }
}

CONFIG_FILE = "gamepad_config.json"

class Colors:
    """ANSI color codes for terminal output"""
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    WHITE = "\033[0;37m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

class GamepadConfig:
    def __init__(self):
        """Initialize the gamepad configuration manager"""
        self.config = self.load_config()
        self.joystick = None

        print(f"{Colors.GREEN}Gamepad configuration initialized{Colors.RESET}")
        # Initialize only joystick subsystem, avoid display/audio to prevent D-Bus issues
        if not pygame.get_init():
            pygame.init()
            # Immediately quit any potentially problematic subsystems
            try:
                # Check if mixer module is available before quitting it
                if hasattr(pygame, 'mixer') and pygame.mixer:
                    pygame.mixer.quit()
            except (AttributeError, ImportError):
                # Module not available, ignore error
                pass
            print(f"{Colors.GREEN}Pygame initialized with limited subsystems{Colors.RESET}")

        # Make sure joystick module is initialized
        if not pygame.joystick.get_init():
            pygame.joystick.init()
            print(f"{Colors.GREEN}Pygame joystick module initialized{Colors.RESET}")

    def load_config(self):
        """Load configuration from file or create default config"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                print(f"{Colors.GREEN}Configuration loaded from {CONFIG_FILE}{Colors.RESET}")
                return config
            except (json.JSONDecodeError, IOError) as e:
                print(f"{Colors.RED}Error loading configuration: {e}{Colors.RESET}")
                print(f"{Colors.YELLOW}Using default configuration{Colors.RESET}")
                return DEFAULT_CONFIG.copy()
        else:
            print(f"{Colors.YELLOW}No configuration file found. Using default configuration.{Colors.RESET}")
            return DEFAULT_CONFIG.copy()

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
            print(f"{Colors.GREEN}Configuration saved to {CONFIG_FILE}{Colors.RESET}")
            return True
        except IOError as e:
            print(f"{Colors.RED}Error saving configuration: {e}{Colors.RESET}")
            return False

    def connect_gamepad(self):
        """Connect to the first available gamepad"""
        if pygame.joystick.get_count() < 1:
            print(f"{Colors.RED}No gamepads found. Please connect a gamepad.{Colors.RESET}")
            return False

        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        name = self.joystick.get_name()
        print(f"{Colors.GREEN}Connected to: {name}{Colors.RESET}")
        return True

    def display_gamepad_info(self):
        """Display information about the connected gamepad"""
        if not self.joystick:
            print(f"{Colors.RED}No gamepad connected{Colors.RESET}")
            return

        name = self.joystick.get_name()
        num_axes = self.joystick.get_numaxes()
        num_buttons = self.joystick.get_numbuttons()
        num_hats = self.joystick.get_numhats()

        print(f"\n{Colors.CYAN}{Colors.BOLD}Gamepad Information:{Colors.RESET}")
        print(f"  Name: {name}")
        print(f"  Number of axes: {num_axes}")
        print(f"  Number of buttons: {num_buttons}")
        print(f"  Number of hats: {num_hats}")

    def calibrate_axis(self, axis_name, axis_index):
        """Calibrate a specific axis of the gamepad"""
        if not self.joystick:
            print(f"{Colors.RED}No gamepad connected{Colors.RESET}")
            return False

        print(f"\n{Colors.CYAN}{Colors.BOLD}Calibrating {axis_name}{Colors.RESET}")
        print(f"Move the {axis_name} to its minimum position and press Space...")

        # Wait for Space key
        min_value = 0
        while True:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    min_value = self.joystick.get_axis(axis_index)
                    print(f"Minimum value recorded: {min_value:.3f}")
                    break
            else:
                # Display current value
                current = self.joystick.get_axis(axis_index)
                print(f"\rCurrent value: {current:.3f}", end="")
                time.sleep(0.1)
                continue
            break

        print(f"\nMove the {axis_name} to its maximum position and press Space...")

        # Wait for Space key
        max_value = 0
        while True:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    max_value = self.joystick.get_axis(axis_index)
                    print(f"Maximum value recorded: {max_value:.3f}")
                    break
            else:
                # Display current value
                current = self.joystick.get_axis(axis_index)
                print(f"\rCurrent value: {current:.3f}", end="")
                time.sleep(0.1)
                continue
            break

        # Ask if values should be inverted
        print(f"\nDo you want to invert the {axis_name}? (y/n)")
        invert = input().strip().lower() == 'y'

        # Update configuration
        if axis_name == "throttle":
            self.config["calibration"]["throttle_min"] = min_value
            self.config["calibration"]["throttle_max"] = max_value
            self.config["calibration"]["invert_throttle"] = invert
        elif axis_name == "steering":
            self.config["calibration"]["steering_min"] = min_value
            self.config["calibration"]["steering_max"] = max_value
            self.config["calibration"]["invert_steering"] = invert

        return True

    def map_control(self, control_name, control_type):
        """Map a control to a button or axis"""
        if not self.joystick:
            print(f"{Colors.RED}No gamepad connected{Colors.RESET}")
            return False

        print(f"\n{Colors.CYAN}{Colors.BOLD}Mapping {control_name}{Colors.RESET}")

        if control_type == "button":
            print(f"Press the button you want to use for {control_name}...")

            while True:
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        button = event.button
                        print(f"{control_name} mapped to button {button}")
                        self.config["controls"][f"{control_name}_btn"] = button
                        return True
                time.sleep(0.1)

        elif control_type == "axis":
            print(f"Move the axis you want to use for {control_name}...")

            # Detect significant axis movement
            baseline = []
            for i in range(self.joystick.get_numaxes()):
                baseline.append(self.joystick.get_axis(i))

            while True:
                for i in range(self.joystick.get_numaxes()):
                    current = self.joystick.get_axis(i)
                    if abs(current - baseline[i]) > 0.5:
                        print(f"{control_name} mapped to axis {i}")
                        self.config["controls"][f"{control_name}_axis"] = i
                        return True
                time.sleep(0.1)

        return False

    def set_deadzone(self, control_name):
        """Set deadzone for a specific control"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}Setting {control_name} deadzone{Colors.RESET}")
        print(f"Current deadzone: {self.config['calibration'][f'{control_name}_deadzone']}")
        print(f"Enter new deadzone value (0.0 to 1.0):")

        try:
            value = float(input().strip())
            if 0.0 <= value <= 1.0:
                self.config["calibration"][f"{control_name}_deadzone"] = value
                print(f"Deadzone set to {value}")
                return True
            else:
                print(f"{Colors.RED}Invalid value. Must be between 0.0 and 1.0{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}Invalid input. Please enter a number.{Colors.RESET}")

        return False

    def set_performance(self, param_name):
        """Set a performance parameter"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}Setting {param_name}{Colors.RESET}")
        print(f"Current value: {self.config['performance'][param_name]}")

        if param_name == "control_mode":
            print("Available modes: duty_cycle, rpm, current")
            print("Enter new mode:")
            mode = input().strip()
            if mode in ["duty_cycle", "rpm", "current"]:
                self.config["performance"]["control_mode"] = mode
                print(f"Control mode set to {mode}")
                return True
            else:
                print(f"{Colors.RED}Invalid mode. Must be duty_cycle, rpm, or current{Colors.RESET}")
                return False
        else:
            print(f"Enter new value:")
            try:
                value = float(input().strip())
                if value >= 0:
                    self.config["performance"][param_name] = value
                    print(f"{param_name} set to {value}")
                    return True
                else:
                    print(f"{Colors.RED}Invalid value. Must be greater than or equal to 0{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}Invalid input. Please enter a number.{Colors.RESET}")

        return False

    def configure_servo_settings(self):
        """Configure the servo settings"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}Configuration du Servomoteur{Colors.RESET}")

        print(f"\nActiver le contrôle du servomoteur? (actuellement: {'activé' if self.config['servo']['enabled'] else 'désactivé'}) (o/n):")
        choice = input().strip().lower()
        if choice == 'o' or choice == 'oui' or choice == 'y' or choice == 'yes':
            self.config['servo']['enabled'] = True
        elif choice == 'n' or choice == 'non' or choice == 'no':
            self.config['servo']['enabled'] = False
            print("Contrôle du servomoteur désactivé.")
            return

        print(f"\nEntrer la position centrale (direction tout droit, 0.0-1.0, actuellement: {self.config['servo']['center_position']}):")
        try:
            value = float(input().strip())
            if 0.0 <= value <= 1.0:
                self.config['servo']['center_position'] = value
            else:
                print(f"{Colors.RED}Valeur invalide. Doit être entre 0.0 et 1.0{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}Entrée invalide. Veuillez entrer un nombre.{Colors.RESET}")

        print(f"\nEntrer la position minimale (complètement à gauche, 0.0-1.0, actuellement: {self.config['servo']['min_position']}):")
        try:
            value = float(input().strip())
            if 0.0 <= value <= 1.0:
                self.config['servo']['min_position'] = value
            else:
                print(f"{Colors.RED}Valeur invalide. Doit être entre 0.0 et 1.0{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}Entrée invalide. Veuillez entrer un nombre.{Colors.RESET}")

        print(f"\nEntrer la position maximale (complètement à droite, 0.0-1.0, actuellement: {self.config['servo']['max_position']}):")
        try:
            value = float(input().strip())
            if 0.0 <= value <= 1.0:
                self.config['servo']['max_position'] = value
            else:
                print(f"{Colors.RED}Valeur invalide. Doit être entre 0.0 et 1.0{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}Entrée invalide. Veuillez entrer un nombre.{Colors.RESET}")

        print(f"\nInverser la direction du servomoteur? (actuellement: {'inversé' if self.config['servo']['invert_direction'] else 'normal'}) (o/n):")
        choice = input().strip().lower()
        if choice == 'o' or choice == 'oui' or choice == 'y' or choice == 'yes':
            self.config['servo']['invert_direction'] = True
        elif choice == 'n' or choice == 'non' or choice == 'no':
            self.config['servo']['invert_direction'] = False

        print(f"\n{Colors.GREEN}Paramètres du servomoteur mis à jour.{Colors.RESET}")

    def run_calibration_menu(self):
        """Run the main calibration menu"""
        # Add environment variables to prevent D-Bus issues
        os.environ["SDL_AUDIODRIVER"] = "dummy"
        os.environ["SDL_DBUS_SCREENSAVER_INHIBIT"] = "0"
        os.environ["SDL_VIDEODRIVER"] = "dummy"

        # Initialize joystick if not already done
        if not pygame.joystick.get_init():
            pygame.joystick.init()

        if not self.connect_gamepad():
            print("No gamepad found for live testing.")
            print("You can still configure settings that don't require a gamepad.")

            # Simplified menu when no gamepad is connected
            running = True
            while running:
                # Clear the screen
                os.system('cls' if os.name == 'nt' else 'clear')

                print(f"\n{Colors.CYAN}{Colors.BOLD}=== Configuration Menu (No Gamepad) ==={Colors.RESET}")
                print(f"{Colors.YELLOW}1. Set Max Duty Cycle{Colors.RESET}")
                print(f"{Colors.YELLOW}2. Set Control Mode{Colors.RESET}")
                print(f"{Colors.YELLOW}3. Configure Servo Settings{Colors.RESET}")
                print(f"{Colors.YELLOW}4. Save Configuration{Colors.RESET}")
                print(f"{Colors.YELLOW}5. Reset to Default Configuration{Colors.RESET}")
                print(f"{Colors.YELLOW}0. Exit{Colors.RESET}")

                choice = input("\nEnter your choice: ").strip()

                if choice == "1":
                    self.set_performance("max_duty_cycle")
                elif choice == "2":
                    self.set_performance("control_mode")
                elif choice == "3":
                    self.configure_servo_settings()
                elif choice == "4":
                    self.save_config()
                elif choice == "5":
                    self.config = DEFAULT_CONFIG.copy()
                    print(f"{Colors.YELLOW}Configuration reset to defaults{Colors.RESET}")
                elif choice == "0":
                    running = False
                else:
                    print(f"{Colors.RED}Invalid choice. Please try again.{Colors.RESET}")

                if running:
                    input("\nPress Enter to continue...")

            print(f"{Colors.GREEN}Configuration complete!{Colors.RESET}")
            return

        self.display_gamepad_info()

        running = True
        while running:
            # Clear the screen
            os.system('cls' if os.name == 'nt' else 'clear')

            print(f"\n{Colors.CYAN}{Colors.BOLD}=== Gamepad Calibration and Configuration ==={Colors.RESET}")
            print(f"{Colors.YELLOW}1. Calibrate Throttle{Colors.RESET}")
            print(f"{Colors.YELLOW}2. Calibrate Steering{Colors.RESET}")
            print(f"{Colors.YELLOW}3. Map Throttle Axis{Colors.RESET}")
            print(f"{Colors.YELLOW}4. Map Steering Axis{Colors.RESET}")
            print(f"{Colors.YELLOW}5. Map Emergency Stop Button{Colors.RESET}")
            print(f"{Colors.YELLOW}6. Map Boost Button{Colors.RESET}")
            print(f"{Colors.YELLOW}7. Map Reverse Button{Colors.RESET}")
            print(f"{Colors.YELLOW}8. Set Throttle Deadzone{Colors.RESET}")
            print(f"{Colors.YELLOW}9. Set Steering Deadzone{Colors.RESET}")
            print(f"{Colors.YELLOW}10. Set Max Duty Cycle{Colors.RESET}")
            print(f"{Colors.YELLOW}11. Set Control Mode{Colors.RESET}")
            print(f"{Colors.YELLOW}12. Test Current Configuration{Colors.RESET}")
            print(f"{Colors.YELLOW}13. Save Configuration{Colors.RESET}")
            print(f"{Colors.YELLOW}14. Reset to Default Configuration{Colors.RESET}")
            print(f"{Colors.YELLOW}15. Configure Servo Settings{Colors.RESET}")
            print(f"{Colors.YELLOW}0. Exit{Colors.RESET}")

            choice = input("\nEnter your choice: ").strip()

            if choice == "1":
                self.calibrate_axis("throttle", self.config["controls"]["throttle_axis"])
            elif choice == "2":
                self.calibrate_axis("steering", self.config["controls"]["steering_axis"])
            elif choice == "3":
                self.map_control("throttle", "axis")
            elif choice == "4":
                self.map_control("steering", "axis")
            elif choice == "5":
                self.map_control("emergency_stop", "button")
            elif choice == "6":
                self.map_control("boost", "button")
            elif choice == "7":
                self.map_control("reverse", "button")
            elif choice == "8":
                self.set_deadzone("throttle")
            elif choice == "9":
                self.set_deadzone("steering")
            elif choice == "10":
                self.set_performance("max_duty_cycle")
            elif choice == "11":
                self.set_performance("control_mode")
            elif choice == "12":
                self.test_configuration()
            elif choice == "13":
                self.save_config()
            elif choice == "14":
                self.config = DEFAULT_CONFIG.copy()
                print(f"{Colors.YELLOW}Configuration reset to defaults{Colors.RESET}")
            elif choice == "15":
                self.configure_servo_settings()
            elif choice == "0":
                running = False
            else:
                print(f"{Colors.RED}Invalid choice. Please try again.{Colors.RESET}")

            if running:
                input("\nPress Enter to continue...")

        pygame.quit()
        print(f"{Colors.GREEN}Calibration complete!{Colors.RESET}")

    def test_configuration(self):
        """Test the current configuration"""
        if not self.joystick:
            print(f"{Colors.RED}No gamepad connected{Colors.RESET}")
            return

        print(f"\n{Colors.CYAN}{Colors.BOLD}Testing Configuration{Colors.RESET}")
        print("Move the controls to see the mapped values")
        print("Press ESC to exit test mode")

        # Get control mappings
        throttle_axis = self.config["controls"]["throttle_axis"]
        steering_axis = self.config["controls"]["steering_axis"]
        emergency_btn = self.config["controls"]["emergency_stop_btn"]
        boost_btn = self.config["controls"]["boost_btn"]
        reverse_btn = self.config["controls"]["reverse_btn"]

        # Calibration settings
        throttle_dz = self.config["calibration"]["throttle_deadzone"]
        steering_dz = self.config["calibration"]["steering_deadzone"]
        invert_throttle = self.config["calibration"]["invert_throttle"]
        invert_steering = self.config["calibration"]["invert_steering"]

        # Servo settings
        servo_enabled = self.config["servo"]["enabled"] if "servo" in self.config else False
        if servo_enabled:
            center_position = self.config["servo"]["center_position"]
            min_position = self.config["servo"]["min_position"]
            max_position = self.config["servo"]["max_position"]
            invert_direction = self.config["servo"]["invert_direction"]

        testing = True
        clock = pygame.time.Clock()

        while testing:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    testing = False

            # Get raw values
            raw_throttle = self.joystick.get_axis(throttle_axis)
            raw_steering = self.joystick.get_axis(steering_axis)

            # Apply inversion if configured
            if invert_throttle:
                raw_throttle = -raw_throttle
            if invert_steering:
                raw_steering = -raw_steering

            # Apply deadzone
            if abs(raw_throttle) < throttle_dz:
                throttle = 0.0
            else:
                throttle = raw_throttle

            if abs(raw_steering) < steering_dz:
                steering = 0.0
            else:
                steering = raw_steering

            # Calculate servo position if servo is enabled
            servo_pos = "N/A"
            if servo_enabled:
                steering_value = steering
                if invert_direction:
                    steering_value = -steering_value

                # Map steering to servo range
                if steering_value < 0:  # Turn left
                    servo_pos = center_position + (steering_value * (center_position - min_position))
                else:  # Turn right or straight
                    servo_pos = center_position + (steering_value * (max_position - center_position))

                # Ensure within bounds
                servo_pos = max(min_position, min(servo_pos, max_position))
                servo_pos = round(servo_pos, 2)

            # Get button states
            e_stop = self.joystick.get_button(emergency_btn)
            boost = self.joystick.get_button(boost_btn)
            reverse = self.joystick.get_button(reverse_btn)

            # Clear the line and print the current values
            print(f"\rThrottle: {throttle:+.2f} | Steering: {steering:+.2f} | Servo: {servo_pos} | E-Stop: {'ON' if e_stop else 'off'} | Boost: {'ON' if boost else 'off'} | Reverse: {'ON' if reverse else 'off'}", end="")

            clock.tick(30)  # 30 FPS

        print("\nTest complete")

    def get_control_value(self, control_name, default=0.0):
        """Get a normalized control value from the gamepad"""
        if not self.joystick:
            return default

        if control_name == "throttle":
            axis = self.config["controls"]["throttle_axis"]
            deadzone = self.config["calibration"]["throttle_deadzone"]
            raw_value = self.joystick.get_axis(axis)

            # Apply inversion if configured
            if self.config["calibration"]["invert_throttle"]:
                raw_value = -raw_value

            # Apply deadzone
            if abs(raw_value) < deadzone:
                return 0.0

            return raw_value

        elif control_name == "steering":
            axis = self.config["controls"]["steering_axis"]
            deadzone = self.config["calibration"]["steering_deadzone"]
            raw_value = self.joystick.get_axis(axis)

            # Apply inversion if configured
            if self.config["calibration"]["invert_steering"]:
                raw_value = -raw_value

            # Apply deadzone
            if abs(raw_value) < deadzone:
                return 0.0

            return raw_value

        return default

    def is_button_pressed(self, button_name):
        """Check if a button is pressed"""
        if not self.joystick:
            return False

        button_key = f"{button_name}_btn"
        if button_key in self.config["controls"]:
            button_index = self.config["controls"][button_key]
            return self.joystick.get_button(button_index)

        return False


if __name__ == "__main__":
    # Run the calibration menu if executed directly
    config = GamepadConfig()
    config.run_calibration_menu()