cmake_minimum_required(VERSION 3.10)
project(gamecar2pad)

find_package(Python3 REQUIRED COMPONENTS Interpreter Development)

add_executable(gamecar2pad
    main.cpp
    Python.cpp
)

target_include_directories(gamecar2pad PRIVATE ${Python3_INCLUDE_DIRS})

target_link_libraries(gamecar2pad
    ${Python3_LIBRARIES}
    dl
    m
)
