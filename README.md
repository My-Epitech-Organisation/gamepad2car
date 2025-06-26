# Gamepad2Car

A Python-based controller for driving an RC car or robot using a gamepad with PyVESC.

## Features

- **Gamepad Control**: Use any gamepad (optimized for Logitech F710) to control your vehicle
- **Video Game-Like Controls**: Includes boost, reverse gear toggle, and cruise control
- **Gamepad Configuration**: Both terminal-based and graphical interface for calibration and remapping
- **Customizable**: Adjust sensitivity, deadzones, and performance parameters
- **VESC Integration**: Controls VESC-based motors via PyVESC protocol

## Requirements

- Python 3.6+
- pygame
- pyvesc
- pyserial
- tkinter (for GUI configuration)
- A compatible gamepad (Logitech F710 recommended)
- A VESC-based motor controller

## Quick Start

1. Clone this repository
2. Connect your gamepad and VESC
3. Run the launcher script:

    ```bash
    ./launch.sh
    ```

## Gamepad Configuration

To configure your gamepad (recommended for first-time setup), you have two options:

### Terminal-Based Configuration

```bash
./launch.sh --config
```

Or alternatively:

```bash
./gamepad_config.py
```

### Graphical Interface Configuration (Recommended)

```bash
./launch.sh --gui
```

Or alternatively:

```bash
./gamepad_gui.py
```

The graphical configuration utility provides:
- Visual feedback of gamepad inputs
- Easy button and axis remapping with visual aids
- Interactive axis calibration with real-time preview
- Performance settings tuning with sliders
- Live testing of your configuration

## Video Game-Style Controls

| Control              | Default Button/Axis      | Function                                   |
|----------------------|--------------------------|-------------------------------------------|
| Right Trigger (RT)   | Axis 4                   | Throttle (forward acceleration)           |
| Left Trigger (LT)    | Axis 2                   | Brake (reverse/deceleration)               |
| Left Stick Left/Right| Axis 0 (Horizontal)      | Steering                                   |
| A Button             | Button 0                 | Boost (temporary speed increase)           |
| B Button             | Button 1                 | Emergency Stop (immediate brake)           |
| X Button             | Button 2                 | Toggle Reverse Gear                        |
| Y Button             | Button 3                 | Toggle Cruise Control                      |

## Command Line Options

The launcher script supports the following options:

```
./launch.sh [options]

Options:
  -c, --config    Launch in terminal-based configuration mode
  -g, --gui       Launch the graphical configuration interface
  -h, --help      Display help message
```

## Customization

Settings are stored in `gamepad_config.json` after calibration. You can either:
1. Use the configuration interfaces to adjust settings
2. Manually edit this file to fine-tune settings

## Troubleshooting

- **Gamepad not detected**: Ensure it's properly connected and powered on
- **VESC not detected**: Check the connection and permissions (`sudo chmod 666 /dev/ttyACM0`)
- **Controls not working correctly**: Run the configuration utility to calibrate
- **GUI doesn't start**: Make sure you have tkinter installed (`sudo apt-get install python3-tk`)

## License

MIT License