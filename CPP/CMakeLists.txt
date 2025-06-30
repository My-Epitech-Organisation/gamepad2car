cmake_minimum_required(VERSION 3.10)
project(gamepad2car)

find_package(Python3 REQUIRED COMPONENTS Interpreter Development)

add_executable(gamepad2car
    main.cpp
    Python.cpp
    Controller.cpp
)

target_include_directories(gamepad2car PRIVATE ${Python3_INCLUDE_DIRS})

target_link_libraries(gamepad2car
    ${Python3_LIBRARIES}
    dl
    m
    pthread
    util
    sfml
)
