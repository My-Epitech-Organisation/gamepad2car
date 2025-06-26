#!/usr/bin/env python3
"""
test_audio_devices.py - Test and list available audio devices
"""

import os
import pygame
import subprocess

def list_audio_devices():
    """List available audio devices using system commands"""
    print("=== Available Audio Devices ===")
    
    try:
        # List PulseAudio sinks (output devices)
        print("\nPulseAudio Output Devices:")
        result = subprocess.run(['pactl', 'list', 'short', 'sinks'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        print(f"  Device {parts[0]}: {parts[1]}")
        else:
            print("  Could not list PulseAudio devices")
    except Exception as e:
        print(f"  Error listing PulseAudio devices: {e}")
    
    try:
        # List ALSA devices
        print("\nALSA Devices:")
        result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("  Could not list ALSA devices")
    except Exception as e:
        print(f"  Error listing ALSA devices: {e}")

def test_pygame_audio_devices():
    """Test different audio device configurations with pygame"""
    print("\n=== Testing Pygame Audio Devices ===")
    
    # Test configurations
    configs = [
        {
            "name": "USB Audio Device (device 0)",
            "env": {"SDL_AUDIODRIVER": "pulse"},
            "pre_init": {"devicename": "0", "frequency": 22050, "size": -16, "channels": 2, "buffer": 1024}
        },
        {
            "name": "Default PulseAudio",
            "env": {"SDL_AUDIODRIVER": "pulse"},
            "pre_init": {"frequency": 22050, "size": -16, "channels": 2, "buffer": 1024}
        },
        {
            "name": "ALSA device 0",
            "env": {"SDL_AUDIODRIVER": "alsa"},
            "pre_init": {"devicename": "hw:0", "frequency": 22050, "size": -16, "channels": 2, "buffer": 1024}
        },
        {
            "name": "ALSA device 1",
            "env": {"SDL_AUDIODRIVER": "alsa"},
            "pre_init": {"devicename": "hw:1", "frequency": 22050, "size": -16, "channels": 2, "buffer": 1024}
        },
        {
            "name": "Default settings",
            "env": {},
            "pre_init": {}
        }
    ]
    
    for config in configs:
        print(f"\nTesting: {config['name']}")
        
        # Set environment variables
        for key, value in config['env'].items():
            os.environ[key] = value
        
        try:
            # Quit any existing mixer
            if pygame.mixer.get_init():
                pygame.mixer.quit()
            
            # Pre-initialize with specific settings
            if config['pre_init']:
                pygame.mixer.pre_init(**config['pre_init'])
            
            # Initialize mixer
            pygame.mixer.init()
            
            # Check if it worked
            if pygame.mixer.get_init():
                freq, format, channels = pygame.mixer.get_init()
                print(f"  ✓ Success: {freq}Hz, {channels} channels, format {format}")
                
                # Test playing a simple tone
                try:
                    # Create a simple beep sound
                    import numpy as np
                    duration = 0.2  # seconds
                    sample_rate = freq
                    t = np.linspace(0, duration, int(sample_rate * duration), False)
                    frequency_hz = 440  # A4 note
                    wave = np.sin(frequency_hz * 2 * np.pi * t)
                    
                    # Convert to pygame sound format
                    wave = (wave * 32767).astype(np.int16)
                    stereo_wave = np.array([wave, wave]).T
                    
                    sound = pygame.sndarray.make_sound(stereo_wave)
                    sound.play()
                    
                    import time
                    time.sleep(0.3)  # Let the sound play
                    sound.stop()
                    
                    print(f"  ✓ Audio playback test successful")
                    
                except Exception as e:
                    print(f"  ⚠ Audio init OK but playback failed: {e}")
                
            else:
                print(f"  ✗ Failed to initialize")
                
        except Exception as e:
            print(f"  ✗ Failed: {e}")
        
        finally:
            # Clean up
            if pygame.mixer.get_init():
                pygame.mixer.quit()
    
    # Reset environment
    for key in ["SDL_AUDIODRIVER"]:
        if key in os.environ:
            del os.environ[key]

def test_sound_file_on_usb():
    """Test playing the actual horn sound file on USB device"""
    print("\n=== Testing Horn Sound on USB Device ===")
    
    # Set to use USB audio device
    os.environ['SDL_AUDIODRIVER'] = 'pulse'
    
    try:
        # Initialize with USB device
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=1024, devicename='0')
        pygame.mixer.init()
        print("✓ USB audio device initialized")
        
        # Look for sound file
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
            print("✗ No horn sound file found")
            return False
        
        # Play the sound
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play()
        print("✓ Horn sound playing on USB device...")
        
        input("Press Enter when you hear the sound (or after a few seconds)...")
        
        pygame.mixer.music.stop()
        print("✓ Test completed")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    finally:
        if pygame.mixer.get_init():
            pygame.mixer.quit()

def main():
    """Main test function"""
    print("=== Audio Device Detection and Testing ===")
    
    # List system audio devices
    list_audio_devices()
    
    # Test pygame configurations
    test_pygame_audio_devices()
    
    # Test actual horn sound on USB
    test_sound_file_on_usb()
    
    print("\n=== Test Complete ===")
    print("If the USB device test worked, your gamepad2car will use that device for horn sounds.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
