import pygame
import sys
import os
import time
import threading
import serial
import serial.tools.list_ports
import pyvesc
from pyvesc.VESC.messages import SetDutyCycle, SetCurrentBrake

class GamepadVESCController:
    def __init__(self, serial_port=None, baudrate=115200):
        # Initialize pygame
        pygame.init()
        pygame.joystick.init()

        # VESC connection parameters
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.serial_connection = None
        self.connected = False

        # Control parameters
        self.throttle = 0.0  # Range from -1.0 to 1.0
        self.steering = 0.0  # Range from -1.0 to 1.0

        # Constraints for safety
        self.max_duty_cycle = 0.3  # Maximum 30% duty cycle for safety
        self.max_steering = 0.5
        
        # Control modes
        self.DRIVE_MODE_NORMAL = 0
        self.DRIVE_MODE_SPORT = 1
        self.DRIVE_MODE_ECO = 2
        self.drive_mode = self.DRIVE_MODE_NORMAL
        self.drive_mode_names = ["NORMAL", "SPORT", "ECO"]
        self.drive_mode_multipliers = [1.0, 1.5, 0.7]  # Throttle multipliers for each mode
        
        # Driving state
        self.is_cruise_control_active = False
        self.cruise_control_speed = 0.0
        
        # Deadzone for sticks (to prevent drift)
        self.stick_deadzone = 0.05
        
        # Throttle and brake response curves
        self.throttle_curve = 2.0  # Higher value = more aggressive exponential response
        self.brake_curve = 1.5     # Higher value = more aggressive exponential response
        
        # Button press tracking
        self.button_states = {}
        self.button_press_time = {}

        # Thread control
        self.running = False
        self.control_thread = None

        # Gamepad configuration for F710
        self.joystick = None
        self.connected_gamepad = False
        
        # Standard F710 mapping
        # Axes
        self.LEFT_STICK_X_AXIS = 0
        self.LEFT_STICK_Y_AXIS = 1
        self.RIGHT_STICK_X_AXIS = 3
        self.RIGHT_STICK_Y_AXIS = 4
        self.LEFT_TRIGGER_AXIS = 2  # Ranges from -1 (unpressed) to 1 (fully pressed)
        self.RIGHT_TRIGGER_AXIS = 5  # Ranges from -1 (unpressed) to 1 (fully pressed)
        self.DPAD_X_AXIS = 6
        self.DPAD_Y_AXIS = 7
        
        # Buttons
        self.A_BUTTON = 0
        self.B_BUTTON = 1
        self.X_BUTTON = 2
        self.Y_BUTTON = 3
        self.LEFT_BUMPER = 4
        self.RIGHT_BUMPER = 5
        self.BACK_BUTTON = 6
        self.START_BUTTON = 7
        self.LEFT_STICK_BUTTON = 8
        self.RIGHT_STICK_BUTTON = 9
        
        # Function mapping
        self.THROTTLE_AXIS = self.RIGHT_TRIGGER_AXIS
        self.BRAKE_AXIS = self.LEFT_TRIGGER_AXIS
        self.STEERING_AXIS = self.LEFT_STICK_X_AXIS
        self.EMERGENCY_STOP_BUTTON = self.B_BUTTON
        self.CRUISE_CONTROL_BUTTON = self.A_BUTTON
        self.DRIVE_MODE_BUTTON = self.X_BUTTON

        # Try to find and connect to the gamepad
        self.find_gamepad()

        # Connect to VESC if port provided, otherwise auto-detect
        if self.serial_port is None:
            self.find_vesc()
        else:
            self.connect_vesc()

    def find_gamepad(self):
        """Find and initialize the Logitech F710 gamepad"""
        joystick_count = pygame.joystick.get_count()

        if joystick_count == 0:
            print("No gamepad detected. Please connect F710 gamepad.")
            return False

        for i in range(joystick_count):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            name = joystick.get_name()

            # Check if this is the F710 or any Logitech gamepad
            if "F710" in name or "Logitech" in name:
                self.joystick = joystick
                self.connected_gamepad = True
                print(f"Connected to gamepad: {name}")
                
                # Initialize button states
                for i in range(self.joystick.get_numbuttons()):
                    self.button_states[i] = False
                    self.button_press_time[i] = 0
                
                return True

        # If no F710 found but there is a joystick, use the first one
        if joystick_count > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Connected to gamepad: {self.joystick.get_name()}")
            self.connected_gamepad = True
            
            # Initialize button states
            for i in range(self.joystick.get_numbuttons()):
                self.button_states[i] = False
                self.button_press_time[i] = 0
                
            return True

        return False

    def find_vesc(self):
        """Automatically find the VESC serial port"""
        print("Searching for VESC...")
        ports = list(serial.tools.list_ports.comports())

        if not ports:
            print("No serial ports found. Make sure VESC is connected.")
            return False

        # Try each port until we find the VESC
        for port in ports:
            print(f"Trying port: {port.device}")
            try:
                self.serial_port = port.device
                if self.connect_vesc():
                    print(f"Found VESC on port: {port.device}")
                    return True
            except:
                pass

        print("VESC not found. Please connect the VESC or specify port manually.")
        return False

    def connect_vesc(self):
        """Connect to the VESC using the serial port"""
        try:
            self.serial_connection = serial.Serial(self.serial_port, baudrate=self.baudrate, timeout=0.05)
            self.connected = True
            print(f"Connected to VESC on {self.serial_port}")
            return True
        except Exception as e:
            self.connected = False
            print(f"Failed to connect to VESC: {e}")
            return False

    def disconnect_vesc(self):
        """Disconnect from the VESC"""
        if self.serial_connection and self.connected:
            # Stop the motors before disconnecting
            self.send_duty_cycle(0)
            time.sleep(0.1)  # Give it a moment to send the stop command

            self.serial_connection.close()
            self.connected = False
            print("Disconnected from VESC")

    def send_duty_cycle(self, duty_cycle):
        """Send a duty cycle command to the VESC using pyvesc

        Args:
            duty_cycle: Float between -1.0 and 1.0
        """
        if not self.connected:
            print("Not connected to VESC")
            return

        # Ensure duty cycle is within limits
        duty_cycle = max(min(duty_cycle, self.max_duty_cycle), -self.max_duty_cycle)

        try:
            # Convert duty cycle from float (-1.0 to 1.0) to integer value expected by VESC
            # VESC expects a value in range of -100000 to 100000
            duty_int = int(duty_cycle * 100000)
            
            # Create SetDutyCycle message with integer value
            msg = SetDutyCycle(duty_int)

            # Encode the message
            packet = pyvesc.encode(msg)

            # Send the message
            self.serial_connection.write(packet)
        except Exception as e:
            print(f"Error sending duty cycle command: {e}")

    def send_brake_current(self, current):
        """Send a brake current command to the VESC using pyvesc

        Args:
            current: Float brake current in amps
        """
        if not self.connected:
            return

        try:
            # Convert current from float (amps) to integer value expected by VESC
            # VESC expects current in mA (1A = 1000mA)
            current_int = int(current * 1000)
            
            # Create SetCurrentBrake message with integer value
            msg = SetCurrentBrake(current_int)

            # Encode the message
            packet = pyvesc.encode(msg)

            # Send the message
            self.serial_connection.write(packet)
        except Exception as e:
            print(f"Error sending brake command: {e}")

    def emergency_stop(self):
        """Perform emergency stop"""
        print("‼️ EMERGENCY STOP! ‼️")
        self.throttle = 0.0
        self.cruise_control_speed = 0.0
        self.is_cruise_control_active = False
        self.send_duty_cycle(0)
        self.send_brake_current(5.0)  # Apply brake current

    def apply_deadzone(self, value, deadzone):
        """Apply deadzone to axis values to prevent drift"""
        if abs(value) < deadzone:
            return 0.0
        
        # Rescale the value to maintain full range
        return (value - deadzone * (1 if value > 0 else -1)) / (1 - deadzone)

    def apply_response_curve(self, value, curve):
        """Apply exponential response curve to make controls more intuitive"""
        return abs(value) ** curve * (1 if value >= 0 else -1)

    def button_just_pressed(self, button_id):
        """Detect if a button was just pressed (not held)"""
        current_state = self.joystick.get_button(button_id) == 1
        was_pressed = False
        
        if current_state and not self.button_states[button_id]:
            was_pressed = True
        
        self.button_states[button_id] = current_state
        return was_pressed

    def process_gamepad_input(self):
        """Read and process gamepad input"""
        if not self.connected_gamepad:
            return

        # Process pygame events
        pygame.event.pump()
        
        # Handle drive mode change
        if self.button_just_pressed(self.DRIVE_MODE_BUTTON):
            self.drive_mode = (self.drive_mode + 1) % 3  # Cycle through 3 modes
            print(f"🔄 Drive mode changed to: {self.drive_mode_names[self.drive_mode]}")
        
        # Handle cruise control toggle
        if self.button_just_pressed(self.CRUISE_CONTROL_BUTTON):
            if not self.is_cruise_control_active and self.throttle > 0.05:
                # Activate cruise control at current speed
                self.is_cruise_control_active = True
                self.cruise_control_speed = self.throttle
                print(f"🟢 Cruise control activated at {self.cruise_control_speed:.2f}")
            else:
                # Deactivate cruise control
                self.is_cruise_control_active = False
                print("🔴 Cruise control deactivated")
        
        # Get raw throttle value from right trigger (ranges from -1 to 1)
        raw_throttle = (self.joystick.get_axis(self.THROTTLE_AXIS) + 1) / 2  # Convert to 0-1 range
        
        # Get raw brake value from left trigger (ranges from -1 to 1)
        raw_brake = (self.joystick.get_axis(self.BRAKE_AXIS) + 1) / 2  # Convert to 0-1 range
        
        # Apply response curves
        throttle_value = self.apply_response_curve(raw_throttle, self.throttle_curve)
        brake_value = self.apply_response_curve(raw_brake, self.brake_curve)
        
        # Get steering value from left stick X-axis
        raw_steering = self.joystick.get_axis(self.STEERING_AXIS)
        steering_value = self.apply_deadzone(raw_steering, self.stick_deadzone)
        
        # Apply drive mode multiplier to throttle
        throttle_value *= self.drive_mode_multipliers[self.drive_mode]
        
        # Check emergency stop button
        if self.joystick.get_button(self.EMERGENCY_STOP_BUTTON):
            self.emergency_stop()
            return
        
        # If cruise control is active and brake is pressed, deactivate it
        if self.is_cruise_control_active and brake_value > 0.1:
            self.is_cruise_control_active = False
            print("🔴 Cruise control deactivated by brake")
        
        # Set throttle value
        if self.is_cruise_control_active:
            self.throttle = self.cruise_control_speed
        else:
            self.throttle = throttle_value
        
        # Set steering value
        self.steering = steering_value * self.max_steering
        
        # Apply constraints
        self.throttle = max(min(self.throttle, self.max_duty_cycle), -self.max_duty_cycle)
        self.steering = max(min(self.steering, self.max_steering), -self.max_steering)
        
        # Print status with emojis to make it more readable
        mode_indicator = ["🚗", "🏎️", "🍃"][self.drive_mode]
        cruise_indicator = "⏺️" if self.is_cruise_control_active else "▶️"
        
        status_msg = f"{mode_indicator} {cruise_indicator} Throttle: {self.throttle:.2f}, Steering: {self.steering:.2f}, Brake: {brake_value:.2f}"
        if self.throttle > 0.01 or abs(self.steering) > 0.01 or brake_value > 0.01:
            print(status_msg)
        
        # Send commands to VESC
        if brake_value > 0.1:  # Apply brake if trigger pulled more than 10%
            brake_current = brake_value * 20.0  # Scale to max 20A brake current
            self.send_brake_current(brake_current)
        else:
            # Apply throttle
            self.send_duty_cycle(self.throttle)

    def start_control_loop(self):
        """Start the control loop in a separate thread"""
        if self.running:
            return

        self.running = True
        self.control_thread = threading.Thread(target=self._control_loop)
        self.control_thread.daemon = True
        self.control_thread.start()
        print("Control loop started")

    def stop_control_loop(self):
        """Stop the control loop"""
        self.running = False
        if self.control_thread:
            self.control_thread.join(timeout=1.0)
        print("Control loop stopped")

    def _control_loop(self):
        """Internal control loop function"""
        while self.running:
            # Process gamepad input and send to VESC
            self.process_gamepad_input()

            # Add a small delay to prevent flooding the serial port
            time.sleep(0.05)  # 20 Hz control rate

    def set_max_duty_cycle(self, value):
        """Set the maximum duty cycle (0.0 to 1.0)"""
        self.max_duty_cycle = max(min(float(value), 1.0), 0.0)
        print(f"Maximum duty cycle set to {self.max_duty_cycle:.2f}")

    def run(self):
        """Main execution loop"""
        if not self.connected_gamepad:
            print("Gamepad not connected. Please connect F710 and restart.")
            return

        if not self.connected:
            print("VESC not connected. Please connect VESC and restart.")
            return

        print("\n====== F710 Gamepad to VESC Controller ======")
        print("Enhanced Control scheme:")
        print("- Right Trigger: Throttle/Accelerate")
        print("- Left Trigger: Brake")
        print("- Left Stick: Steering")
        print("- A Button: Toggle Cruise Control")
        print("- B Button: Emergency Stop")
        print("- X Button: Cycle Drive Modes (Normal/Sport/Eco)")
        print("- Back Button: Soft Stop (gradual slowdown)")
        print("- Press Ctrl+C to exit")
        print("==============================================\n")

        # Ask for max duty cycle
        try:
            max_duty_input = input(f"Enter maximum duty cycle (0.0-1.0) [{self.max_duty_cycle}]: ")
            if max_duty_input.strip():
                self.set_max_duty_cycle(max_duty_input)
        except ValueError:
            print(f"Invalid input. Using default max duty cycle: {self.max_duty_cycle}")

        # Start the control loop
        self.start_control_loop()

        try:
            # Keep the main thread alive
            while True:
                time.sleep(0.1)

        except KeyboardInterrupt:
            # Clean exit on Ctrl+C
            print("\nExiting...")

        finally:
            # Clean up
            self.stop_control_loop()
            self.send_duty_cycle(0)  # Stop motors
            self.disconnect_vesc()
            pygame.quit()

def list_available_ports():
    """List all available serial ports"""
    ports = list(serial.tools.list_ports.comports())
    print("\nAvailable serial ports:")
    for i, port in enumerate(ports):
        print(f"{i+1}. {port.device} - {port.description}")
    return ports

def main():
    # Print welcome message
    print("\n====== F710 Gamepad to VESC Controller ======\n")

    # List available serial ports
    ports = list_available_ports()

    # If no ports available, offer to continue anyway
    if not ports:
        print("No serial ports found. VESC auto-detection will fail.")
        continue_anyway = input("Continue anyway? (y/n): ")
        if continue_anyway.lower() != 'y':
            return

    # Ask user to select a port or use auto-detection
    serial_port = None
    if ports:
        choice = input("\nSelect a port number or press Enter for auto-detection: ")
        if choice.strip():
            try:
                port_index = int(choice) - 1
                if 0 <= port_index < len(ports):
                    serial_port = ports[port_index].device
                else:
                    print("Invalid port number. Using auto-detection.")
            except ValueError:
                print("Invalid input. Using auto-detection.")

    # Create controller
    controller = GamepadVESCController(serial_port=serial_port)

    # Run the controller
    controller.run()

if __name__ == "__main__":
    main()