#!/bin/bash
# Script pour compiler et exécuter le programme C++ qui contrôle le VESC via Python

echo "=== Cleaning previous build ==="
rm -rf build
mkdir -p build
cd build

echo "=== Configuring CMake ==="
cmake ..
if [ $? -ne 0 ]; then
    echo "CMake configuration failed!"
    exit 1
fi

echo "=== Building ==="
make
if [ $? -ne 0 ]; then
    echo "Compilation failed!"
    exit 1
fi

echo ""
echo "=== Running VESC Control Test ==="
echo ""
# Exécution du programme
./gamecar2pad

exit 0
