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
        // Joystick droit axe X (U) pour le steering
        float axisU = sf::Joystick::getAxisPosition(this->_joystickId, sf::Joystick::U);
        // Mapping: -100->0 | 0->0.5 | 100->1
        float steering = 0.5f + (axisU / 200.f);
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
            std::cout << "\n>>> Bouton Y pressé ! Klaxon activé !" << std::endl;
            this->playSound("horn");
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

void Controller::_loadMusic(const std::string &id, const std::string &path, float vol)
{
    auto music = std::make_unique<sf::Music>();
    
    if (!music->openFromFile(path)) {
        std::cerr << "Erreur lors du chargement du fichier audio: " << path << std::endl;
        return;
    }
    
    music->setVolume(vol);
    music->setLoop(false);
    
    // Stocker la musique dans la map
    _musicList[id] = std::move(music);
}

void Controller::playSound(const std::string &id)
{
    auto it = _musicList.find(id);
    if (it != _musicList.end() && it->second) {
        it->second->stop();
        it->second->play();
    } else {
        std::cerr << "Son non trouvé: " << id << std::endl;
    }
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
    _loadMusic("horn", "assets/circus_horn.mp3", 100.f);
    this->_mThread = std::thread([this]() {
        this->loop();
    });
}

Controller::~Controller()
{
    this->_isRunning = false;
    if (this->_mThread.joinable()) this->_mThread.join();
}