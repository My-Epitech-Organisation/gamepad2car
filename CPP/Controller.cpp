/*
** EPITECH PROJECT, 2025
** gamepad2car
** File description:
** Controller
*/

#include "Controller.hpp"
#include <SFML/Window/Joystick.hpp>
#include <iostream>
#include <thread>
#include <chrono>

void Controller::loop()
{
    while (this->_isRunning) {
        sf::Joystick::update();
        float axisU = sf::Joystick::getAxisPosition(this->_joystickId, sf::Joystick::U);
        float steering = (axisU + 100.f) / 200.f;
        float triggerDroit = sf::Joystick::getAxisPosition(this->_joystickId, sf::Joystick::R); // entre -100 et 100
        float triggerGauche = sf::Joystick::getAxisPosition(this->_joystickId, sf::Joystick::Z);
        float triggerDroitNorm = triggerDroit > this->_deadZone ? (triggerDroit / 100.f) : 0.f;
        float triggerGaucheNorm = triggerGauche > this->_deadZone ? (triggerGauche / 100.f) : 0.f;
        float speed = 0.f;
        if (triggerDroitNorm > 0.f && triggerGaucheNorm > 0.f) {
            speed = 0.f;
        } else {
            speed = triggerDroitNorm - triggerGaucheNorm;
        }
        if (sf::Joystick::isButtonPressed(this->_joystickId, 3)) {
            std::cout << "\n>>> Bouton Y pressé !" << std::endl;
        }
        this->_mtx.lock();
        this->_speed = speed;
        this->_steering = steering;
        this->_mtx.unlock();
        std::cout << "Steering: " << steering << " | Vitesse: " << speed << "     \r";
        std::cout.flush();
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}

std::unique_ptr<sf::Music> Controller::_initMusic(const std::string & path, float vol)
{
    std::unique_ptr<sf::Music> music = std::make_unique<sf::Music>();

    music->openFromFile(path);
    music->setVolume(vol);
    return music;
}

void playSound()
{
    sf::Music music;
    if (music.openFromFile("nice_music.ogg"))
 
    // Play the music
    music.play();
 
}

float Controller::getSpeed()
{
    std::lock_guard<std::mutex> lock(this->_mtx);

    return this->_speed;
}

float Controller::getSteering()
{
    std::lock_guard<std::mutex> lock(this->_mtx);

    return this->_steering;
}

Controller::Controller()
{
    sf::Joystick::update();
    if (!sf::Joystick::isConnected(this->_joystickId)) {
        std::cerr << "Aucun joystick connecté sur l'ID 0." << std::endl;
        throw std::runtime_error("Error no controller detected");
    }
    this->_musicList.emplace("horn", "assets/circus_horn.mp3");
    this->_mThread = std::thread([this]() {
        this->loop();
    });
}

Controller::~Controller()
{
    this->_isRunning = false;
    if (this->_mThread.joinable()) this->_mThread.join();
}