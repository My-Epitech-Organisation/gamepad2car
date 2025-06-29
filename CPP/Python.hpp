#pragma once
#include <Python.h>
#include <string>
#include <iostream>
#include <optional>
#include <type_traits>

class PythonCaller {
private:
    static bool is_initialized;

public:
    // Initialiser l'interpréteur Python une seule fois
    static void initialize() {
        if (!is_initialized) {
            Py_Initialize();
            
            // Configurer les chemins Python
            PyRun_SimpleString("import sys");
            PyRun_SimpleString("import os");
            PyRun_SimpleString("current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()");
            PyRun_SimpleString("sys.path.append('.')");
            PyRun_SimpleString("sys.path.append('./PyVESC')");
            PyRun_SimpleString("sys.path.append(os.path.join(os.getcwd(), 'PyVESC'))");
            PyRun_SimpleString("print('Initializing Python interpreter')");
            PyRun_SimpleString("print('Current working directory:', os.getcwd())");
            PyRun_SimpleString("print('Python paths:', sys.path)");
            
            is_initialized = true;
        }
    }
    
    // Finaliser l'interpréteur Python à la fin du programme
    static void finalize() {
        if (is_initialized) {
            Py_Finalize();
            is_initialized = false;
        }
    }
    
    template<typename T>
    static PyObject* to_python(const T &value);

    template<typename T>
    static T from_python(PyObject* obj);

    // Fonction qui retourne une valeur depuis Python
    template<typename Ret, typename... Args>
    static std::optional<Ret> call_and_return(const std::string& module_name,
                                              const std::string& function_name,
                                              Args&&... args)
    {
        initialize(); // Initialiser si ce n'est pas déjà fait

        PyRun_SimpleString("import sys");
        PyRun_SimpleString("import os");
        PyRun_SimpleString("current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()");
        PyRun_SimpleString("print('Current working directory:', os.getcwd())");
        PyRun_SimpleString("print('Python paths:', sys.path)");

        PyObject* py_module_name = PyUnicode_FromString(module_name.c_str());
        PyObject* py_module = PyImport_Import(py_module_name);
        Py_DECREF(py_module_name);

        if (!py_module) {
            PyErr_Print();
            std::cerr << "Could not import module: " << module_name << std::endl;
            Py_Finalize();
            return std::nullopt;
        }

        PyObject* py_func = PyObject_GetAttrString(py_module, function_name.c_str());

        if (!py_func || !PyCallable_Check(py_func)) {
            PyErr_Print();
            std::cerr << "Function not found or not callable: " << function_name << std::endl;
            Py_XDECREF(py_func);
            Py_DECREF(py_module);
            Py_Finalize();
            return std::nullopt;
        }

        PyObject* py_args = PyTuple_Pack(sizeof...(Args), to_python(std::forward<Args>(args))...);
        PyObject* result = PyObject_CallObject(py_func, py_args);

        Py_DECREF(py_args);
        Py_DECREF(py_func);
        Py_DECREF(py_module);

        if (!result) {
            PyErr_Print();
            Py_Finalize();
            return std::nullopt;
        }

        Ret value = from_python<Ret>(result);
        Py_DECREF(result);
        
        // Ne pas finaliser ici pour conserver l'état entre les appels
        // Py_Finalize() sera appelé par finalize() à la fin du programme
        return value;
    }
};
