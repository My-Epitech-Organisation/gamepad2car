# Gamepad2Car

A Python-based controller for driving an RC car or robot using a gamepad with PyVESC.

## Features

- **Gamepad Control**: Use any gamepad (optimized for Logitech F710) to control your vehicle
- **Video Game-Like Controls**: Includes boost, reverse gear toggle, and cruise control
- **Gamepad Configuration**: Interactive calibration and remapping interface
- **Customizable**: Adjust sensitivity, deadzones, and performance parameters
- **VESC Integration**: Controls VESC-based motors via PyVESC protocol

## Requirements

- Python 3.6+
- pygame
- pyvesc
- pyserial
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

To configure your gamepad (recommended for first-time setup):

```bash
./launch.sh --config
```

Or alternatively:

```bash
./gamepad_config.py
```

The configuration utility allows you to:
- Calibrate controls
- Remap buttons and axes
- Set deadzone values
- Configure performance parameters
- Test your configuration

## Video Game-Style Controls

| Control              | Default Button/Axis      | Function                                   |
|----------------------|--------------------------|-------------------------------------------|
| Right Stick Up/Down  | Axis 3 (Vertical)        | Throttle (forward/backward)                |
| Left Stick Left/Right| Axis 0 (Horizontal)      | Steering                                   |
| A Button             | Button 0                 | Boost (temporary speed increase)           |
| B Button             | Button 1                 | Emergency Stop (immediate brake)           |
| X Button             | Button 2                 | Toggle Reverse Gear                        |
| Y Button             | Button 3                 | Toggle Cruise Control                      |
| Left Trigger         | Axis 2                   | Brake                                      |

## Command Line Options

The launcher script supports the following options:

```
./launch.sh [options]

Options:
  -c, --config    Launch in gamepad configuration mode
  -h, --help      Display help message
```

## Customization

Settings are stored in `gamepad_config.json` after calibration. You can manually edit this file to fine-tune settings.

## Troubleshooting

- **Gamepad not detected**: Ensure it's properly connected and powered on
- **VESC not detected**: Check the connection and permissions (`sudo chmod 666 /dev/ttyACM0`)
- **Controls not working correctly**: Run the configuration utility to calibrate

## License

MIT License