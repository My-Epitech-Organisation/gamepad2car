/*
** EPITECH PROJECT, 2025
** gamepad2car
** File description:
** Test programme pour la manette SFML
*/

#include <SFML/Window/Joystick.hpp>
#include <iostream>
#include <iomanip>
#include <thread>
#include <chrono>
#include <map>
#include <string>

// Structure pour stocker les informations sur les axes
struct AxisInfo {
    std::string name;
    sf::Joystick::Axis axis;
};

class JoystickTester {
private:
    int _joystickId;
    float _deadZone;
    std::map<sf::Joystick::Axis, AxisInfo> _axisMap;
    bool _isRunning;

    void initAxisMap() {
        _axisMap[sf::Joystick::X] = {"Stick Gauche X", sf::Joystick::X};
        _axisMap[sf::Joystick::Y] = {"Stick Gauche Y", sf::Joystick::Y};
        _axisMap[sf::Joystick::U] = {"Stick Droit X", sf::Joystick::U};
        _axisMap[sf::Joystick::V] = {"Stick Droit Y", sf::Joystick::V};
        _axisMap[sf::Joystick::Z] = {"Trigger Gauche", sf::Joystick::Z};
        _axisMap[sf::Joystick::R] = {"Trigger Droit", sf::Joystick::R};
        _axisMap[sf::Joystick::PovX] = {"D-Pad X", sf::Joystick::PovX};
        _axisMap[sf::Joystick::PovY] = {"D-Pad Y", sf::Joystick::PovY};
    }

    void clearScreen() {
        std::cout << "\033[2J\033[H"; // Clear screen and move cursor to top-left
    }

    void displayAxes() {
        clearScreen();
        std::cout << "=== Test Manette ID " << _joystickId << " ===" << std::endl;
        std::cout << "Deadzone: " << _deadZone << std::endl << std::endl;

        // Afficher les valeurs des axes
        std::cout << "=== AXES ===" << std::endl;
        for (const auto& [axis, info] : _axisMap) {
            float value = sf::Joystick::getAxisPosition(_joystickId, axis);
            float normalizedValue = std::abs(value) < _deadZone ? 0.0f : value;
            
            // Créer une barre de progression
            const int barWidth = 30;
            int pos = (normalizedValue + 100.0f) * barWidth / 200.0f;
            
            std::cout << std::setw(15) << info.name << ": ";
            std::cout << std::fixed << std::setprecision(2) << std::setw(7) << normalizedValue << " [";
            
            for (int i = 0; i < barWidth; ++i) {
                if (i == barWidth/2) std::cout << "|";
                else if (i == pos) std::cout << "*";
                else std::cout << "-";
            }
            std::cout << "]" << std::endl;
        }

        // Afficher l'état des boutons
        std::cout << "\n=== BOUTONS ===" << std::endl;
        int buttonCount = sf::Joystick::getButtonCount(_joystickId);
        for (int i = 0; i < buttonCount; ++i) {
            bool isPressed = sf::Joystick::isButtonPressed(_joystickId, i);
            std::cout << "Bouton " << i << ": " << (isPressed ? "PRESSÉ   " : "relâché  ");
            if ((i + 1) % 4 == 0) std::cout << std::endl;
        }
        std::cout << std::endl;

        // Instructions
        std::cout << "\nAppuyez sur le bouton B (1) pour quitter" << std::endl;
    }

public:
    JoystickTester(int joystickId = 0, float deadZone = 10.0f)
        : _joystickId(joystickId), _deadZone(deadZone), _isRunning(true)
    {
        initAxisMap();
    }

    bool init() {
        sf::Joystick::update();
        if (!sf::Joystick::isConnected(_joystickId)) {
            std::cerr << "Erreur: Aucune manette connectée sur l'ID " << _joystickId << std::endl;
            return false;
        }
        
        std::cout << "Manette détectée: ID " << _joystickId << std::endl;
        std::cout << "Nombre de boutons: " << sf::Joystick::getButtonCount(_joystickId) << std::endl;
        std::cout << "Démarrage du test..." << std::endl;
        std::this_thread::sleep_for(std::chrono::seconds(1));
        
        return true;
    }

    void run() {
        while (_isRunning) {
            sf::Joystick::update();
            
            // Afficher les informations
            displayAxes();
            
            // Vérifier le bouton de sortie (B)
            if (sf::Joystick::isButtonPressed(_joystickId, 1)) {
                _isRunning = false;
            }
            
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }
    }
};

int main(int argc, char *argv[])
{
    int joystickId = 0;
    float deadZone = 10.0f;

    // Parser les arguments
    if (argc > 1) joystickId = std::atoi(argv[1]);
    if (argc > 2) deadZone = std::atof(argv[2]);

    JoystickTester tester(joystickId, deadZone);
    
    if (!tester.init()) {
        return 1;
    }

    tester.run();
    std::cout << "Test terminé." << std::endl;
    
    return 0;
}
