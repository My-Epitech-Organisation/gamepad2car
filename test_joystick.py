#!/usr/bin/env python3
"""
test_joystick.py - Simple script to test joystick initialization without display
"""

import os
import sys

# Configure environment variables to prevent D-Bus issues
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["SDL_DBUS_SCREENSAVER_INHIBIT"] = "0"
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import time

def main():
    print("Starting joystick test...")
    
    # Initialize pygame without initializing display
    pygame.init()
    
    # Immediately quit potentially problematic subsystems
    pygame.mixer.quit()
    
    # Make sure joystick module is explicitly initialized
    if not pygame.joystick.get_init():
        pygame.joystick.init()
    
    print(f"Joystick module initialized: {pygame.joystick.get_init()}")
    print(f"Number of joysticks: {pygame.joystick.get_count()}")
    
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print(f"Connected to: {joystick.get_name()}")
        print(f"Number of axes: {joystick.get_numaxes()}")
        print(f"Number of buttons: {joystick.get_numbuttons()}")
        print(f"Number of hats: {joystick.get_numhats()}")
        
        # Test reading some values
        print("\nMoving joystick will display axis values. Press Ctrl+C to exit.")
        try:
            while True:
                pygame.event.pump()  # Process events
                values = []
                for i in range(joystick.get_numaxes()):
                    values.append(f"{joystick.get_axis(i):.2f}")
                
                print(f"\rAxes: {', '.join(values)}", end="")
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nTest terminated by user")
    else:
        print("No joystick/gamepad found.")
    
    pygame.quit()
    print("Test completed")

if __name__ == "__main__":
    main()
