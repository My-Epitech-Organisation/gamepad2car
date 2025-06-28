#!/bin/bash
# Script pour compiler et exécuter le programme C++ qui contrôle le VESC via Python

echo "=== Update Submodule ==="
git submodule update --init --recursive

./setup_vesc_environment.sh

echo "=== Building C++ VESC Control Program ==="
mkdir -p build
cd build

# Génération avec CMake
cmake ..
if [ $? -ne 0 ]; then
    echo "CMake configuration failed!"
    exit 1
fi

# Compilation
make
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
