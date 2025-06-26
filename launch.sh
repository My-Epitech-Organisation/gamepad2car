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
#pip install --upgrade -r requirements.txt
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

# Patch PyVESC library for compatibility
SETTERS_FILE="$VENV_DIR/lib64/python3.13/site-packages/pyvesc/VESC/messages/setters.py"
if [ -f "$SETTERS_FILE" ]; then
    echo -e "${YELLOW}Patching PyVESC library for compatibility...${NC}"
    # Create a backup if it doesn't already exist
    if [ ! -f "${SETTERS_FILE}.bak" ]; then
        cp "$SETTERS_FILE" "${SETTERS_FILE}.bak"
        echo -e "${GREEN}Created backup of original file at ${SETTERS_FILE}.bak${NC}"
    fi
    
    # Patch the file using sed to replace the line
    sed -i "s/('duty_cycle', 'i', 100000)/('duty_cycle', 'i')/g" "$SETTERS_FILE"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Successfully patched PyVESC library${NC}"
    else
        echo -e "${RED}Failed to patch PyVESC library${NC}"
    fi
else
    echo -e "${YELLOW}Could not find PyVESC setters.py file at expected location:${NC}"
    echo -e "${YELLOW}$SETTERS_FILE${NC}"
    echo -e "${YELLOW}Will try to continue anyway...${NC}"
    
    # Try to find the file in other locations
    FOUND_FILES=$(find $VENV_DIR -name "setters.py" | grep pyvesc)
    if [ ! -z "$FOUND_FILES" ]; then
        echo -e "${GREEN}Found potential PyVESC files at:${NC}"
        echo -e "$FOUND_FILES"
        echo -e "${YELLOW}Please update the SETTERS_FILE variable in launch.sh to the correct path${NC}"
    fi
fi

# Launch the application
echo -e "${YELLOW}Launching Gamepad2Car application...${NC}"

# Set environment variables to prevent D-Bus issues on Jetson Nano
export SDL_AUDIODRIVER="dummy"
export SDL_DBUS_SCREENSAVER_INHIBIT="0"

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
