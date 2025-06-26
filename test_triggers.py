#!/usr/bin/env python3
"""
test_triggers.py - Test trigger functionality for gamepad2car
"""

import os
import sys
import time

# Set environment variables to prevent D-Bus issues
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["SDL_DBUS_SCREENSAVER_INHIBIT"] = "0"
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame

def test_triggers():
    """Test trigger detection and values"""
    print("Testing trigger functionality...")
    
    # Initialize pygame
    pygame.init()
    pygame.joystick.init()
    
    # Check for gamepad
    if pygame.joystick.get_count() < 1:
        print("✗ No gamepad detected. Please connect a gamepad.")
        return False
    
    # Initialize first gamepad
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    
    name = joystick.get_name()
    num_axes = joystick.get_numaxes()
    
    print(f"✓ Gamepad detected: {name}")
    print(f"✓ Number of axes: {num_axes}")
    
    # Common trigger axes for different controllers
    trigger_axes = {
        "RT (Right Trigger)": [4, 5, 9],  # Common right trigger axes
        "LT (Left Trigger)": [2, 4, 8]    # Common left trigger axes
    }
    
    print("\nTesting all axes - press triggers to see values:")
    print("Press Ctrl+C to exit test")
    
    try:
        while True:
            pygame.event.pump()  # Process events
            
            # Clear the screen
            print("\033[2J\033[H", end="")  # Clear screen and move cursor to top
            
            print(f"Gamepad: {name}")
            print("=" * 50)
            
            # Show all axis values
            for i in range(num_axes):
                raw_value = joystick.get_axis(i)
                
                # Convert trigger values (if this is a trigger axis)
                converted_value = (raw_value + 1.0) / 2.0 if i in [2, 4, 5] else raw_value
                
                axis_type = ""
                if i == 0:
                    axis_type = " (Left Stick X)"
                elif i == 1:
                    axis_type = " (Left Stick Y)"
                elif i == 2:
                    axis_type = " (LT - Left Trigger)"
                elif i == 3:
                    axis_type = " (Right Stick X)"
                elif i == 4:
                    axis_type = " (RT - Right Trigger / Right Stick Y)"
                elif i == 5:
                    axis_type = " (RT - Right Trigger)"
                
                print(f"Axis {i:2d}{axis_type}: Raw={raw_value:+.3f} | Trigger={converted_value:.3f}")
            
            print("\n" + "=" * 50)
            print("Instructions:")
            print("- Press RT (Right Trigger) for throttle")
            print("- Press LT (Left Trigger) for brake") 
            print("- Move Left Stick X for steering")
            print("- Press Ctrl+C to exit")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nTest terminated by user")
    
    # Cleanup
    pygame.quit()
    return True

if __name__ == "__main__":
    print("=== Trigger Test for GamePad2Car ===")
    print("This test will help you identify the correct axis numbers for your triggers")
    
    success = test_triggers()
    
    if success:
        print("\n✓ Trigger test completed!")
        print("\nRecommended configuration:")
        print("- RT (Right Trigger): Usually axis 4 or 5")
        print("- LT (Left Trigger): Usually axis 2")
        print("- Left Stick X: Usually axis 0")
        print("\nUpdate your gamepad_config.json with the correct axis numbers.")
    else:
        print("\n✗ Trigger test failed. Make sure your gamepad is connected.")
