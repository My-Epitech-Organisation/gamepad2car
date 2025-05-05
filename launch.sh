#!/bin/bash

# Script to setup and launch the gamepad2car application

# Set color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Define the virtual environment directory
VENV_DIR="venv"

# Parse command line arguments
CONFIG_MODE=false
GUI_MODE=false
HELP_MODE=false

for arg in "$@"; do
  case $arg in
    --config|-c)
      CONFIG_MODE=true
      shift
      ;;
    --gui|-g)
      GUI_MODE=true
      shift
      ;;
    --help|-h)
      HELP_MODE=true
      shift
      ;;
    *)
      # Unknown option
      ;;
  esac
done

# Display help if requested
if [ "$HELP_MODE" = true ]; then
  echo -e "${CYAN}=== Gamepad2Car Launcher ===${NC}"
  echo "Usage: ./launch.sh [options]"
  echo ""
  echo "Options:"
  echo "  -c, --config    Launch in gamepad configuration mode (terminal UI)"
  echo "  -g, --gui       Launch the graphical configuration interface"
  echo "  -h, --help      Display this help message"
  echo ""
  echo "This script sets up a virtual environment and launches the gamepad2car application."
  exit 0
fi

echo -e "${CYAN}=== Gamepad2Car Launcher ===${NC}"
echo "Setting up virtual environment and launching application..."

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment. Is python3-venv installed?${NC}"
        echo "Try: sudo apt-get install python3-venv"
        exit 1
    fi
    echo -e "${GREEN}Virtual environment created.${NC}"
else
    echo -e "${GREEN}Using existing virtual environment.${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source $VENV_DIR/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to activate virtual environment.${NC}"
    exit 1
fi

# Install/upgrade requirements
echo -e "${YELLOW}Installing required packages...${NC}"
pip install --upgrade -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install requirements.${NC}"
    deactivate
    exit 1
fi
echo -e "${GREEN}Requirements installed successfully.${NC}"

# Check for VESC connection
echo -e "${YELLOW}Checking for VESC connection...${NC}"
VESC_PORT="/dev/ttyACM0"
if [ -e "$VESC_PORT" ]; then
    echo -e "${GREEN}VESC device found at $VESC_PORT${NC}"
    # Try to set permissions if not already readable/writable
    if [ ! -r "$VESC_PORT" ] || [ ! -w "$VESC_PORT" ]; then
        echo -e "${YELLOW}Setting permissions for VESC device...${NC}"
        sudo chmod 666 $VESC_PORT
    fi
else
    echo -e "${YELLOW}VESC device not found at $VESC_PORT${NC}"
    echo "If your VESC is connected to a different port, you can configure it in the settings."
    echo "You can still configure your gamepad without a VESC connected."
fi

# Check for gamepad
echo -e "${YELLOW}Checking for gamepad...${NC}"
if [ -e "/dev/input/js0" ]; then
    echo -e "${GREEN}Gamepad device found.${NC}"
else
    echo -e "${YELLOW}Gamepad device not found. Please connect your gamepad.${NC}"
    echo "Make sure the gamepad is powered on and properly connected."
fi

# Launch the application
echo -e "${YELLOW}Launching Gamepad2Car application...${NC}"

if [ "$GUI_MODE" = true ]; then
    echo -e "${CYAN}Running in graphical configuration mode${NC}"
    ./gamepad_gui.py
elif [ "$CONFIG_MODE" = true ]; then
    echo -e "${CYAN}Running in terminal configuration mode${NC}"
    ./gamepad2car.py --config
else
    ./gamepad2car.py
fi

# Deactivate virtual environment on exit
deactivate
echo -e "${GREEN}Exited. Virtual environment deactivated.${NC}"