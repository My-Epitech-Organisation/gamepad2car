#!/usr/bin/env python3
"""
test_sound.py - Test sound functionality for gamepad2car
"""

import os
import pygame

def test_sound():
    """Test the sound system"""
    print("Testing sound system...")
    
    # Set audio device to USB PnP Audio Device (card 2, device 0)
    os.environ['SDL_AUDIODRIVER'] = 'alsa'  # Use ALSA driver for better device control
    
    # Try different methods to force USB audio device
    usb_audio_attempts = [
        {'devicename': 'hw:2,0'},  # Direct ALSA device specification (card 2, device 0)
        {'devicename': 'plughw:2,0'},  # ALSA with plugin layer
        {'devicename': 'USB Audio'},  # By name
        {'devicename': 'USB PnP Audio Device'},  # Full name
    ]
    
    mixer_initialized = False
    for i, attempt in enumerate(usb_audio_attempts):
        try:
            print(f"Attempting to initialize with device: {attempt['devicename']}")
            pygame.mixer.quit()  # Clean previous attempt
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024, **attempt)
            pygame.mixer.init()
            print(f"✓ Pygame mixer initialized successfully with USB audio device: {attempt['devicename']}")
            mixer_initialized = True
            break
        except Exception as e:
            print(f"✗ Attempt {i+1} failed: {e}")
    
    if not mixer_initialized:
        print("Trying with default settings...")
        try:
            pygame.mixer.quit()
            pygame.mixer.init()
            print("✓ Pygame mixer initialized with default device")
        except Exception as e:
            print(f"✗ Failed to initialize pygame mixer: {e}")
            return False
    
    # Check for sound file
    sound_paths = [
        "assets/circus_horn.mp3",
        "./assets/circus_horn.mp3",
        os.path.join(os.path.dirname(__file__), "assets", "circus_horn.mp3")
    ]
    
    sound_file = None
    for path in sound_paths:
        if os.path.exists(path):
            sound_file = path
            print(f"✓ Sound file found: {path}")
            break
    
    if not sound_file:
        print("✗ No sound file found. Expected locations:")
        for path in sound_paths:
            print(f"  - {path}")
        return False
    
    # Test sound playback
    try:
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play()
        print("✓ Sound playback started successfully")
        
        # Wait for user input
        input("Press Enter when you hear the sound (or if no sound is heard)...")
        
        pygame.mixer.music.stop()
        print("✓ Sound test completed")
        
    except Exception as e:
        print(f"✗ Error playing sound: {e}")
        return False
    
    # Cleanup
    pygame.mixer.quit()
    print("✓ Pygame mixer cleaned up")
    
    return True

if __name__ == "__main__":
    print("=== Sound Test for GamePad2Car ===")
    success = test_sound()
    
    if success:
        print("\n✓ All sound tests passed!")
    else:
        print("\n✗ Some sound tests failed. Check the error messages above.")
        print("Make sure you have:")
        print("  1. A sound file at assets/circus_horn.mp3")
        print("  2. Proper audio system setup")
        print("  3. Required Python packages installed (pygame)")
