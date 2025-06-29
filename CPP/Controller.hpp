/*
** EPITECH PROJECT, 2025
** gamepad2car
** File description:
** Controller
*/

#ifndef CONTROLLER_HPP_
#define CONTROLLER_HPP_
#include <thread>
#include <atomic>
#include <mutex>
#include <map>
#include <memory>
#include <SFML/Audio.hpp>

class Controller {
    private:
        int _joystickId = 0;
        float _deadZone = 10.0f;
        float _speed;
        float _steering;
        std::map<std::string, sf::Music> _musicList;
        std::mutex _mtx;
        std::thread _mThread;
        std::atomic<bool> _isRunning = true;

        std::unique_ptr<sf::Music> _initMusic(const std::string &path, float volume = 50.f);
    public:
        void loop();
        float getSpeed();
        float getSteering();
        void playSound(const std::string &id);

        Controller();
        ~Controller();
};

#endif /* !CONTROLLER_HPP_ */
