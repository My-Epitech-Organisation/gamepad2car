#!/bin/bash
# Script pour compiler et exécuter le programme C++ qui contrôle le VESC via Python

echo "=== Update Submodule ==="
git submodule update --init --recursive

mv setters.py.move PyVESC/pyvesc/VESC/messages/setters.py

./setup_vesc_environment.sh

echo "=== Building C++ VESC Control Program ==="
mkdir -p build
cd build

# Génération avec CMake
cmake .. -DPython3_EXECUTABLE=/usr/local/bin/python3.10 \
      -DPython3_INCLUDE_DIR=/usr/local/include/python3.10 \
      -DPython3_LIBRARY=/usr/local/lib/libpython3.10.so
if [ $? -ne 0 ]; then
    echo "CMake configuration failed!"
    exit 1
fi

# Compilation
cmake --build .
if [ $? -ne 0 ]; then
    echo "Compilation failed!"
    exit 1
fi

echo ""
echo "=== Copy bin files ==="
echo ""
    cp gamecar2pad ../ && cd ..

echo ""
echo "=== Running VESC Control Test ==="
echo ""
# Exécution du programme
./gamecar2pad

exit 0
