/*
** EPITECH PROJECT, 2025
** gamepad2car
** File description:
** Python
*/

#include "Python.hpp"

// --- SPECIALISATIONS ---

template<>
PyObject* PythonCaller::to_python<int>(const int &value) {
    return PyLong_FromLong(value);
}

template<>
PyObject* PythonCaller::to_python<double>(const double &value) {
    return PyFloat_FromDouble(value);
}

template<>
PyObject* PythonCaller::to_python<const char*>(const char* const& value) {
    return PyUnicode_FromString(value);
}

template<>
PyObject* PythonCaller::to_python<std::string>(const std::string& value) {
    return PyUnicode_FromString(value.c_str());
}


template<>
int PythonCaller::from_python<int>(PyObject* obj) {
    return static_cast<int>(PyLong_AsLong(obj));
}

template<>
double PythonCaller::from_python<double>(PyObject* obj) {
    return PyFloat_AsDouble(obj);
}

template<>
std::string PythonCaller::from_python<std::string>(PyObject* obj) {
    return std::string(PyUnicode_AsUTF8(obj));
}
