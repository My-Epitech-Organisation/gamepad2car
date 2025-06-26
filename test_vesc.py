#!/usr/bin/env python3
"""
test_vesc.py - Test VESC connectivity and functionality for gamepad2car
"""

import os
import sys
import json
import serial.tools.list_ports
from serial import Serial, SerialException
import time

try:
    import pyvesc
    from pyvesc import encode
    from pyvesc.VESC.messages.setters import SetDutyCycle, SetRPM, SetCurrent, SetCurrentBrake, SetServoPosition
    from pyvesc.VESC.messages.getters import GetValues
    PYVESC_AVAILABLE = True
except ImportError:
    PYVESC_AVAILABLE = False
    print("Warning: PyVESC not available, only basic serial tests will be performed")

# Load configuration
CONFIG_FILE = "gamepad_config.json"

def load_config():
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading configuration: {e}")
            return None
    else:
        print(f"No configuration file found: {CONFIG_FILE}")
        return None

def list_serial_ports():
    """List all available serial ports"""
    print("\n=== Available Serial Ports ===")
    available_ports = list(serial.tools.list_ports.comports())
    
    if not available_ports:
        print("No serial ports found.")
        return []
    
    for port in available_ports:
        print(f"  Port: {port.device}")
        print(f"    Description: {port.description}")
        print(f"    Hardware ID: {port.hwid}")
        print()
    
    return [port.device for port in available_ports]

def test_serial_connection(port, baud_rate=115200):
    """Test basic serial connection"""
    print(f"\n=== Testing Serial Connection ===")
    print(f"Port: {port}")
    print(f"Baud Rate: {baud_rate}")
    
    try:
        # Test opening the port
        ser = Serial(port, baud_rate, timeout=1)
        print("✓ Serial port opened successfully")
        
        # Test if port is accessible
        if ser.is_open:
            print("✓ Serial port is open and accessible")
        else:
            print("✗ Serial port failed to open")
            return False
            
        # Close the connection
        ser.close()
        print("✓ Serial port closed successfully")
        return True
        
    except SerialException as e:
        print(f"✗ Serial connection failed: {e}")
        print("Possible solutions:")
        print("  1. Check if the VESC is connected and powered on")
        print("  2. Verify the correct port is being used")
        print("  3. Check permissions with: ls -l /dev/tty*")
        print(f"  4. Try: sudo chmod 666 {port}")
        print("  5. Add your user to dialout group: sudo usermod -a -G dialout $USER")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_vesc_communication(port, baud_rate=115200):
    """Test VESC communication using PyVESC"""
    if not PYVESC_AVAILABLE:
        print("\n=== VESC Communication Test Skipped ===")
        print("PyVESC not available. Install with: pip install git+https://github.com/LiamBindle/PyVESC.git")
        return False
    
    print(f"\n=== Testing VESC Communication ===")
    
    try:
        # Open serial connection
        ser = Serial(port, baud_rate, timeout=0.5)
        print("✓ Serial connection established")
        
        # Test sending a safe command (duty cycle 0)
        print("Testing duty cycle command (0% throttle)...")
        msg = SetDutyCycle(0)  # 0% duty cycle - safe
        packet = encode(msg)
        ser.write(packet)
        print("✓ Duty cycle command sent successfully")
        
        # Wait a bit
        time.sleep(0.1)
        
        # Test servo command (center position)
        print("Testing servo command (center position)...")
        servo_msg = SetServoPosition(0.5)  # Center position
        servo_packet = encode(servo_msg)
        ser.write(servo_packet)
        print("✓ Servo command sent successfully")
        
        # Test reading values (if supported)
        try:
            print("Testing values request...")
            get_values_msg = GetValues()
            get_values_packet = encode(get_values_msg)
            ser.write(get_values_packet)
            
            # Try to read response (may timeout if not supported)
            response = ser.read(100)
            if response:
                print(f"✓ Received response ({len(response)} bytes)")
            else:
                print("? No response to values request (may be normal)")
                
        except Exception as e:
            print(f"? Values request failed: {e} (may be normal)")
        
        ser.close()
        print("✓ VESC communication test completed")
        return True
        
    except Exception as e:
        print(f"✗ VESC communication failed: {e}")
        print("Possible causes:")
        print("  1. VESC firmware may not support PyVESC protocol")
        print("  2. Wrong baud rate or port configuration")
        print("  3. VESC may be in a different communication mode")
        print("  4. Hardware connection issues")
        return False

def test_configuration():
    """Test the loaded configuration"""
    print("\n=== Configuration Test ===")
    
    config = load_config()
    if not config:
        print("✗ No configuration loaded")
        return False
    
    print("✓ Configuration file loaded")
    
    # Check VESC-related settings
    performance = config.get('performance', {})
    
    serial_port = performance.get('serial_port', '/dev/ttyACM0')
    baud_rate = performance.get('baud_rate', 115200)
    control_mode = performance.get('control_mode', 'duty_cycle')
    max_duty_cycle = performance.get('max_duty_cycle', 0.3)
    max_rpm = performance.get('max_rpm', 5000)
    max_current = performance.get('max_current', 10)
    
    print(f"  Serial Port: {serial_port}")
    print(f"  Baud Rate: {baud_rate}")
    print(f"  Control Mode: {control_mode}")
    print(f"  Max Duty Cycle: {max_duty_cycle}")
    print(f"  Max RPM: {max_rpm}")
    print(f"  Max Current: {max_current}A")
    
    # Validate settings
    issues = []
    
    if max_duty_cycle > 1.0:
        issues.append("Max duty cycle is greater than 1.0 (100%)")
    elif max_duty_cycle > 0.5:
        issues.append("Max duty cycle is greater than 50% - be careful!")
    
    if control_mode not in ['duty_cycle', 'rpm', 'current']:
        issues.append(f"Invalid control mode: {control_mode}")
    
    if max_current > 50:
        issues.append("Max current is very high - be careful!")
    
    if baud_rate not in [9600, 19200, 38400, 57600, 115200]:
        issues.append(f"Unusual baud rate: {baud_rate}")
    
    # Check servo settings
    servo = config.get('servo', {})
    if servo.get('enabled', False):
        print("\n  Servo Control: Enabled")
        print(f"    Center Position: {servo.get('center_position', 0.5)}")
        print(f"    Min Position: {servo.get('min_position', 0.0)}")
        print(f"    Max Position: {servo.get('max_position', 1.0)}")
        print(f"    Invert Direction: {servo.get('invert_direction', False)}")
    else:
        print("\n  Servo Control: Disabled")
    
    if issues:
        print("\n⚠️  Configuration Issues:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("\n✓ Configuration looks good")
    
    return len(issues) == 0

def main():
    """Main test function"""
    print("=== VESC Connectivity and Configuration Test ===")
    print("This script will test your VESC setup for gamepad2car\n")
    
    # Test 1: List available ports
    available_ports = list_serial_ports()
    
    # Test 2: Check configuration
    config_ok = test_configuration()
    
    # Test 3: Get the port to test
    config = load_config()
    if config:
        test_port = config.get('performance', {}).get('serial_port', '/dev/ttyACM0')
        test_baud = config.get('performance', {}).get('baud_rate', 115200)
    else:
        test_port = '/dev/ttyACM0'
        test_baud = 115200
    
    # If the configured port is not available, let user choose
    if test_port not in available_ports and available_ports:
        print(f"\nConfigured port {test_port} not found.")
        print("Available ports:")
        for i, port in enumerate(available_ports):
            print(f"  {i+1}. {port}")
        
        try:
            choice = input("\nEnter port number to test (or press Enter to skip): ").strip()
            if choice:
                idx = int(choice) - 1
                if 0 <= idx < len(available_ports):
                    test_port = available_ports[idx]
                else:
                    print("Invalid choice, skipping connection test.")
                    return
        except (ValueError, KeyboardInterrupt):
            print("Skipping connection test.")
            return
    
    # Test 4: Basic serial connection
    if test_port in available_ports or os.path.exists(test_port):
        serial_ok = test_serial_connection(test_port, test_baud)
        
        # Test 5: VESC communication
        if serial_ok:
            vesc_ok = test_vesc_communication(test_port, test_baud)
        else:
            vesc_ok = False
    else:
        print(f"\nPort {test_port} not available, skipping connection tests.")
        serial_ok = False
        vesc_ok = False
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Configuration: {'✓ OK' if config_ok else '✗ Issues found'}")
    print(f"Serial Connection: {'✓ OK' if serial_ok else '✗ Failed'}")
    print(f"VESC Communication: {'✓ OK' if vesc_ok else '✗ Failed'}")
    
    if not (config_ok and serial_ok and vesc_ok):
        print("\n⚠️  Some tests failed. Please check the issues above.")
        print("Common solutions:")
        print("  1. Make sure your VESC is connected and powered on")
        print("  2. Check USB cable and connections")
        print("  3. Verify VESC firmware supports PyVESC protocol")
        print("  4. Run: sudo chmod 666 /dev/ttyACM*")
        print("  5. Add user to dialout group: sudo usermod -a -G dialout $USER")
        print("  6. Run configuration tool: python gamepad2car.py --config")
    else:
        print("\n✅ All tests passed! Your VESC setup looks good.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("Please report this issue if it persists.")
