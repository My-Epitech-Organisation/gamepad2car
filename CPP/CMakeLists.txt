cmake_minimum_required(VERSION 3.10)
project(gamepad2car)

find_package(Python3 REQUIRED COMPONENTS Interpreter Development)

add_executable(gamepad2car
    main.cpp
    Python.cpp
    Controller.cpp
)

add_executable(controllerTest
    joystickTestControl.cpp
    Controller.cpp)

target_link_libraries(controllerTest
    sfml-window
    sfml-audio
    pthread)



# Ajouter l'exécutable de test pour la manette
add_executable(joystickTest
    joystickHandle.cpp
)

target_include_directories(gamepad2car PRIVATE ${Python3_INCLUDE_DIRS})

target_link_libraries(gamepad2car
    ${Python3_LIBRARIES}
    dl
    m
    pthread
    util
    sfml-audio
    sfml-window
)

# Lier les bibliothèques SFML pour le test de manette
target_link_libraries(joystickTest
    sfml-window
    pthread
)
