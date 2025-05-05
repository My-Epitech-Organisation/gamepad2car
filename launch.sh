#!/bin/bash

# Script to setup and launch the gamepad2car application

# Set color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Gamepad2Car Launcher ===${NC}"
echo "Setting up virtual environment and launching application..."

# Define the virtual environment directory
VENV_DIR="venv"

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
    echo -e "${RED}VESC device not found at $VESC_PORT${NC}"
    echo "Please check connection and try again."
    echo "If your VESC is connected to a different port, edit the VESC_PORT variable in this script."
fi

# Check for gamepad
echo -e "${YELLOW}Checking for Logitech F710 gamepad...${NC}"
if [ -e "/dev/input/js0" ]; then
    echo -e "${GREEN}Gamepad device found.${NC}"
else
    echo -e "${RED}Gamepad device not found. Please connect your Logitech F710 gamepad.${NC}"
    echo "Make sure the gamepad is in DirectInput mode (D) and the switch is set to ON."
fi

# Launch the application
echo -e "${YELLOW}Launching Gamepad2Car application...${NC}"
./gamepad2car.py

# Deactivate virtual environment on exit
deactivate
echo -e "${GREEN}Exited. Virtual environment deactivated.${NC}"