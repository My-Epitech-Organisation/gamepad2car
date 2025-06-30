/*
** EPITECH PROJECT, 2025
** gamepad2car
** File description:
** controllerList
*/

#include <SFML/Window/Joystick.hpp>
#include <iostream>

int main() {
    for (unsigned int i = 0; i < sf::Joystick::Count; ++i) {
        if (sf::Joystick::isConnected(i)) {
            std::cout << "Joystick " << i << " is connected.\n";
            std::cout << "  Name: " << sf::Joystick::getIdentification(i).name.toAnsiString() << "\n";
            std::cout << "  Button count: " << sf::Joystick::getButtonCount(i) << "\n";
        }
    }
    return 0;
}
