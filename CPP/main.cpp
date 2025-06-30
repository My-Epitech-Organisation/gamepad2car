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
#include "Controller.hpp"

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
    Controller ctrl;
    bool result = call_vesc_function("init_vesc");
    if (!result) {
        std::cerr << "Failed to initialize VESC. Exiting." << std::endl;
        return 1;
    }
    std::cout << "VESC initialized successfully" << std::endl;
    std::cout << "Centering steering..." << std::endl;
    result = call_vesc_function("center_steering");
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    while (true) {
        float speed = ctrl.getSpeed();
        result = call_vesc_function("set_motor_speed", speed);
        float steering = ctrl.getSteering();
        result = call_vesc_function("set_servo_position", steering);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
    std::cout << "Stopping motor..." << std::endl;
    result = call_vesc_function("stop_motor");
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    std::cout << "\nShutting down..." << std::endl;
    result = call_vesc_function("close_vesc");
    PythonCaller::finalize();
    return 0;
}
