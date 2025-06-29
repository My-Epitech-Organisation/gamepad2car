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

// Fonction helper pour appeler les méthodes du wrapper Python
template<typename Ret = std::string, typename... Args>
Ret call_vesc_wrapper(const std::string& function_name, Args&&... args) {
    auto result = PythonCaller::call_and_return<Ret>("vesc_wrapper", function_name, std::forward<Args>(args)...);
    if (!result) {
        std::cerr << "Error calling Python function: " << function_name << std::endl;
        if constexpr (std::is_same_v<Ret, std::string>) {
            return "ERROR";
        } else {
            return Ret{};
        }
    }
    return *result;
}

// Afficher le statut du VESC
void print_vesc_status(const std::string& status) {
    if (status.find("ERROR") != std::string::npos) {
        std::cout << "Error getting status: " << status << std::endl;
        return;
    }

    std::cout << "VESC Status:" << std::endl;
    std::cout << "------------------------" << std::endl;
    
    size_t pos = 0;
    std::string delimiter = "|";
    std::string token;
    std::string s = status;
    
    while ((pos = s.find(delimiter)) != std::string::npos) {
        token = s.substr(0, pos);
        std::cout << token << std::endl;
        s.erase(0, pos + delimiter.length());
    }
    std::cout << s << std::endl;  // Display the last part
    std::cout << "------------------------" << std::endl;
}

int main()
{
    std::cout << "VESC Control Test Program" << std::endl;
    std::cout << "------------------------" << std::endl;
    
    // Initialiser le moteur
    std::string result = call_vesc_wrapper("initialize_motor");
    std::cout << "Motor initialization: " << result << std::endl;
    if (result != "OK") {
        std::cerr << "Failed to initialize motor. Exiting." << std::endl;
        return 1;
    }
    
    // Centre le servo
    std::cout << "Centering steering..." << std::endl;
    result = call_vesc_wrapper("center_steering");
    std::cout << "Result: " << result << std::endl;
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    
    // Récupère le statut initial
    std::string status = call_vesc_wrapper("get_status");
    std::cout << "Initial state:" << std::endl;
    print_vesc_status(status);
    
    // Test de direction
    std::cout << "Testing steering left..." << std::endl;
    result = call_vesc_wrapper("set_steering", 0.2);  // tourner à gauche
    std::cout << "Result: " << result << std::endl;
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    
    std::cout << "Testing steering right..." << std::endl;
    result = call_vesc_wrapper("set_steering", 0.8);  // tourner à droite
    std::cout << "Result: " << result << std::endl;
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    
    std::cout << "Returning to center..." << std::endl;
    result = call_vesc_wrapper("center_steering");
    std::cout << "Result: " << result << std::endl;
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    
    // Test de vitesse (faible)
    std::cout << "Testing forward movement at 10% speed..." << std::endl;
    result = call_vesc_wrapper("set_speed", 0.1);
    std::cout << "Result: " << result << std::endl;
    std::this_thread::sleep_for(std::chrono::milliseconds(2000));
    
    // Arrêt du moteur
    std::cout << "Stopping motor..." << std::endl;
    result = call_vesc_wrapper("stop_motor");
    std::cout << "Result: " << result << std::endl;
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    
    // Récupère le statut final
    status = call_vesc_wrapper("get_status");
    std::cout << "Final state:" << std::endl;
    print_vesc_status(status);
    
    // Arrêt complet et fermeture de la connexion
    std::cout << "Shutting down..." << std::endl;
    result = call_vesc_wrapper("stop");
    std::cout << "Result: " << result << std::endl;
    
    std::cout << "Test completed successfully" << std::endl;
    
    // Finaliser l'interpréteur Python
    PythonCaller::finalize();
    return 0;
}
