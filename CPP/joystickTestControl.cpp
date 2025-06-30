/*
** EPITECH PROJECT, 2025
** gamepad2car
** File description:
** Test du Controller avec affichage des valeurs
*/

#include "Controller.hpp"
#include <iostream>
#include <iomanip>
#include <thread>
#include <chrono>

void clearScreen()
{
    std::cout << "\033[2J\033[H";  // Clear screen and move cursor to top-left
}

void displayBar(float value, int width = 40)
{
    int pos = static_cast<int>((value * width));
    std::cout << "[";
    for (int i = 0; i < width; ++i) {
        if (i == width/2) std::cout << "|";
        else if (i == pos) std::cout << "O";
        else std::cout << "-";
    }
    std::cout << "]";
}

int main()
{
    try {
        Controller ctrl;
        std::cout << "Controller initialisé avec succès!" << std::endl;
        std::cout << "Appuyez sur Ctrl+C pour quitter" << std::endl;
        std::this_thread::sleep_for(std::chrono::seconds(2));

        while (true) {
            clearScreen();
            
            float steering = ctrl.getSteering();
            float speed = ctrl.getSpeed();

            // Afficher le steering
            std::cout << "=== Test Controller ===" << std::endl << std::endl;
            
            std::cout << "DIRECTION (Joystick Droit - Axe X)" << std::endl;
            std::cout << "Valeur: " << std::fixed << std::setprecision(3) << steering;
            std::cout << "  ";
            displayBar(steering);
            std::cout << std::endl;
            std::cout << "Gauche 0.0 " << std::string(15, '-') << " 0.5 " << std::string(15, '-') << " 1.0 Droite" << std::endl;
            std::cout << std::endl;

            // Afficher la vitesse
            std::cout << "VITESSE (Triggers)" << std::endl;
            std::cout << "Valeur: " << std::fixed << std::setprecision(3) << speed;
            std::cout << "  ";
            // Mapper la vitesse de [-1,1] à [0,1] pour l'affichage
            displayBar((speed + 1.0f) / 2.0f);
            std::cout << std::endl;
            std::cout << "Arrière -1.0 " << std::string(13, '-') << " 0.0 " << std::string(13, '-') << " +1.0 Avant" << std::endl;
            std::cout << std::endl;

            // Instructions
            std::cout << "\nContrôles:" << std::endl;
            std::cout << "- Joystick Droit (X): Direction" << std::endl;
            std::cout << "- Trigger Droit: Accélérer" << std::endl;
            std::cout << "- Trigger Gauche: Reculer" << std::endl;
            std::cout << "- Bouton Y: Klaxon" << std::endl;
            std::cout << "\nCtrl+C pour quitter" << std::endl;

            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }
    } catch (const std::exception& e) {
        std::cerr << "Erreur: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
