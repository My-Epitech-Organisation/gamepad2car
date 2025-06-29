/*
** EPITECH PROJECT, 2025
** gamepad2car
** File description:
** main
*/
#include "Python.hpp"
#include <iostream>
#include <string>
#include <optional>
#include <thread>
#include <chrono>

// Fonction helper pour appeler les méthodes de l'API vescLib directement
template<typename Ret = bool, typename... Args>
Ret call_vesc_function(const std::string& function_name, Args&&... args) {
    auto result = PythonCaller::call_and_return<Ret>("vescLib", function_name, std::forward<Args>(args)...);
    if (!result) {
        std::cerr << "Error calling Python function: " << function_name << std::endl;
        if constexpr (std::is_same_v<Ret, bool>) {
            return false;
        } else {
            return Ret{};
        }
    }
    return *result;
}

int main()
{
    std::cout << "VESC Control Test Program" << std::endl;
    std::cout << "------------------------" << std::endl;
    
    // Initialiser le VESC
    std::cout << "Initializing VESC..." << std::endl;
    bool result = call_vesc_function("init_vesc");
    if (!result) {
        std::cerr << "Failed to initialize VESC. Exiting." << std::endl;
        return 1;
    }
    std::cout << "VESC initialized successfully" << std::endl;
    
    // Test de direction 
    // Centre le servo
    std::cout << "\n=== Testing Steering ===\n" << std::endl;
    std::cout << "Centering steering..." << std::endl;
    result = call_vesc_function("center_steering");
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    
    // Tourner à gauche
    std::cout << "Testing steering left..." << std::endl;
    result = call_vesc_function("set_servo_position", 0.2);  // tourner à gauche
    std::this_thread::sleep_for(std::chrono::milliseconds(1500));
    
    // Tourner à droite
    std::cout << "Testing steering right..." << std::endl;
    result = call_vesc_function("set_servo_position", 0.8);  // tourner à droite
    std::this_thread::sleep_for(std::chrono::milliseconds(1500));
    
    // Retour au centre
    std::cout << "Returning to center..." << std::endl;
    result = call_vesc_function("center_steering");
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    
    // Test du moteur
    std::cout << "\n=== Testing Motor ===\n" << std::endl;
    std::cout << "Starting motor at 50% speed..." << std::endl;
    result = call_vesc_function("set_motor_speed", 0.5);
    
    // Laisser tourner pendant 5 secondes
    std::cout << "Running for 5 seconds..." << std::endl;
    std::this_thread::sleep_for(std::chrono::seconds(5));
    
    // Arrêt du moteur
    std::cout << "Stopping motor..." << std::endl;
    result = call_vesc_function("stop_motor");
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    
    // Arrêt complet et fermeture de la connexion
    std::cout << "\nShutting down..." << std::endl;
    result = call_vesc_function("close_vesc");
    
    std::cout << "Test completed successfully" << std::endl;
    
    // Finaliser l'interpréteur Python
    PythonCaller::finalize();
    return 0;
}
