#!/usr/bin/env python3
"""
gamepad_gui.py - Interface graphique pour configurer et calibrer le gamepad
"""

import os
import sys
import json
import time
import tkinter as tk
from tkinter import ttk, messagebox, StringVar, IntVar, DoubleVar
import pygame
from gamepad_config import GamepadConfig, DEFAULT_CONFIG, CONFIG_FILE, Colors


class GamepadGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Configuration Gamepad2Car")
        self.root.geometry("800x650")
        self.root.minsize(800, 650)

        # Style
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        self.style.configure("Title.TLabel", font=("Arial", 14, "bold"))
        self.style.configure("Info.TLabel", foreground="#0066cc")
        self.style.configure("Success.TLabel", foreground="#009900")
        self.style.configure("Warning.TLabel", foreground="#cc6600")
        self.style.configure("Error.TLabel", foreground="#cc0000")

        # Initialize gamepad configuration
        self.config_manager = GamepadConfig()
        self.config = self.config_manager.config

        # Initialize pygame for gamepad input
        if not pygame.get_init():
            pygame.init()
        if not pygame.joystick.get_init():
            pygame.joystick.init()

        self.gamepad_name = StringVar(value="Non connecté")

        # Connect to gamepad
        self.joystick = None
        self.connect_gamepad()

        # Status variables
        self.status_text = StringVar(value="Prêt")

        # For gamepad detection
        self.axis_values = {}
        self.button_states = {}
        self.listening_for = None
        self.detected_input = None

        # Input mapping variables
        self.mapping_vars = {}

        # Create the GUI layout
        self.create_gui()

        # Start the update loop for gamepad feedback
        self.update_gamepad_status()

    def connect_gamepad(self):
        """Connect to the first available gamepad"""
        if pygame.joystick.get_count() > 0:
            if self.joystick is None:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                self.config_manager.joystick = self.joystick
                self.gamepad_name.set(self.joystick.get_name())
                self.status_text.set(f"Connecté à {self.joystick.get_name()}")

                # Initialize axis and button states
                if hasattr(self, 'axes_frame'):
                    self.update_axes_display()
                if hasattr(self, 'buttons_frame'):
                    self.update_buttons_display()

                return True
            return True
        else:
            self.joystick = None
            self.config_manager.joystick = None
            self.gamepad_name.set("Non connecté")
            self.status_text.set("Aucun gamepad détecté. Veuillez connecter un gamepad.")
            return False

    def create_gui(self):
        """Create the main application GUI"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.create_overview_tab()
        self.create_mapping_tab()
        self.create_calibration_tab()
        self.create_performance_tab()
        self.create_test_tab()

        # Bottom status bar
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)

        ttk.Label(self.status_bar, text="État: ").pack(side=tk.LEFT)
        ttk.Label(self.status_bar, textvariable=self.status_text).pack(side=tk.LEFT)

        ttk.Label(self.status_bar, text="  Gamepad: ").pack(side=tk.LEFT)
        ttk.Label(self.status_bar, textvariable=self.gamepad_name).pack(side=tk.LEFT)

        # Buttons at the bottom
        self.button_bar = ttk.Frame(self.root)
        self.button_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)

        ttk.Button(self.button_bar, text="Rafraîchir gamepad", command=self.refresh_gamepad).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_bar, text="Restaurer par défaut", command=self.restore_defaults).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_bar, text="Enregistrer", command=self.save_config).pack(side=tk.RIGHT, padx=5)

    def create_overview_tab(self):
        """Create the overview tab with general information"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Aperçu")

        # Header
        header = ttk.Frame(tab)
        header.pack(fill=tk.X, padx=20, pady=20)

        ttk.Label(header, text="Configuration Gamepad2Car", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(header, text="Interface graphique pour configurer votre gamepad").pack(anchor=tk.W)

        # Gamepad Info Section
        info_frame = ttk.LabelFrame(tab, text="Informations du Gamepad")
        info_frame.pack(fill=tk.X, padx=20, pady=10, ipady=5)

        self.gamepad_info_text = tk.Text(info_frame, height=8, width=70, wrap=tk.WORD, state=tk.DISABLED)
        self.gamepad_info_text.pack(fill=tk.X, padx=10, pady=10)

        # Instructions Section
        help_frame = ttk.LabelFrame(tab, text="Instructions")
        help_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        instructions = """
1. Onglet Mapping: Permet de remapper les boutons et axes de votre gamepad.
2. Onglet Calibration: Permet de calibrer les axes et définir les deadzones.
3. Onglet Performance: Configure les paramètres de performance comme la vitesse maximale.
4. Onglet Test: Vous permet de tester la configuration en temps réel.

Pour remapper une entrée:
- Cliquez sur le bouton "Assigner" à côté du contrôle que vous souhaitez remapper
- Actionnez le bouton ou l'axe de votre gamepad que vous voulez utiliser
- L'entrée sera automatiquement détectée et assignée

Pour calibrer un axe:
- Utilisez les minima et maxima pour définir les limites de l'axe
- Utilisez la deadzone pour éliminer les petits mouvements non intentionnels

N'oubliez pas d'enregistrer votre configuration avant de quitter!
        """

        help_text = tk.Text(help_frame, height=15, width=70, wrap=tk.WORD)
        help_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        help_text.insert(tk.END, instructions)
        help_text.config(state=tk.DISABLED)

        # Set initial gamepad info
        self.update_gamepad_info()

    def create_mapping_tab(self):
        """Create the control mapping tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Mapping")

        # Header
        header = ttk.Frame(tab)
        header.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(header, text="Mapping des contrôles", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(header, text="Assignez les boutons et axes de votre gamepad aux différentes fonctions").pack(anchor=tk.W)

        # Controls Frame
        controls_frame = ttk.LabelFrame(tab, text="Contrôles")
        controls_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Axis Mappings
        ttk.Label(controls_frame, text="Axes", style="Header.TLabel").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)

        # Create variables for axis mappings
        self.mapping_vars["throttle_axis"] = IntVar(value=self.config["controls"]["throttle_axis"])
        self.mapping_vars["brake_axis"] = IntVar(value=self.config["controls"]["brake_axis"])
        self.mapping_vars["steering_axis"] = IntVar(value=self.config["controls"]["steering_axis"])

        # Throttle axis
        ttk.Label(controls_frame, text="Accélérateur:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Label(controls_frame, textvariable=self.mapping_vars["throttle_axis"]).grid(row=1, column=1, padx=10, pady=2)
        ttk.Button(controls_frame, text="Assigner", command=lambda: self.start_listening("throttle_axis")).grid(row=1, column=2, padx=10, pady=2)

        # Brake axis
        ttk.Label(controls_frame, text="Frein:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Label(controls_frame, textvariable=self.mapping_vars["brake_axis"]).grid(row=2, column=1, padx=10, pady=2)
        ttk.Button(controls_frame, text="Assigner", command=lambda: self.start_listening("brake_axis")).grid(row=2, column=2, padx=10, pady=2)

        # Steering axis
        ttk.Label(controls_frame, text="Direction:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Label(controls_frame, textvariable=self.mapping_vars["steering_axis"]).grid(row=3, column=1, padx=10, pady=2)
        ttk.Button(controls_frame, text="Assigner", command=lambda: self.start_listening("steering_axis")).grid(row=3, column=2, padx=10, pady=2)

        # Button Mappings
        ttk.Label(controls_frame, text="Boutons", style="Header.TLabel").grid(row=4, column=0, sticky=tk.W, padx=10, pady=10)

        # Create variables for button mappings
        self.mapping_vars["emergency_stop_btn"] = IntVar(value=self.config["controls"]["emergency_stop_btn"])
        self.mapping_vars["boost_btn"] = IntVar(value=self.config["controls"]["boost_btn"])
        self.mapping_vars["reverse_btn"] = IntVar(value=self.config["controls"]["reverse_btn"])
        self.mapping_vars["cruise_toggle_btn"] = IntVar(value=self.config["controls"]["cruise_toggle_btn"])

        # Emergency stop button
        ttk.Label(controls_frame, text="Arrêt d'urgence:").grid(row=5, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Label(controls_frame, textvariable=self.mapping_vars["emergency_stop_btn"]).grid(row=5, column=1, padx=10, pady=2)
        ttk.Button(controls_frame, text="Assigner", command=lambda: self.start_listening("emergency_stop_btn")).grid(row=5, column=2, padx=10, pady=2)

        # Boost button
        ttk.Label(controls_frame, text="Boost:").grid(row=6, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Label(controls_frame, textvariable=self.mapping_vars["boost_btn"]).grid(row=6, column=1, padx=10, pady=2)
        ttk.Button(controls_frame, text="Assigner", command=lambda: self.start_listening("boost_btn")).grid(row=6, column=2, padx=10, pady=2)

        # Reverse button
        ttk.Label(controls_frame, text="Marche arrière:").grid(row=7, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Label(controls_frame, textvariable=self.mapping_vars["reverse_btn"]).grid(row=7, column=1, padx=10, pady=2)
        ttk.Button(controls_frame, text="Assigner", command=lambda: self.start_listening("reverse_btn")).grid(row=7, column=2, padx=10, pady=2)

        # Cruise control button
        ttk.Label(controls_frame, text="Régulateur de vitesse:").grid(row=8, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Label(controls_frame, textvariable=self.mapping_vars["cruise_toggle_btn"]).grid(row=8, column=1, padx=10, pady=2)
        ttk.Button(controls_frame, text="Assigner", command=lambda: self.start_listening("cruise_toggle_btn")).grid(row=8, column=2, padx=10, pady=2)

        # Status label for mapping feedback
        self.mapping_status = StringVar(value="Cliquez sur 'Assigner' puis actionnez le contrôle souhaité")
        ttk.Label(controls_frame, textvariable=self.mapping_status, style="Info.TLabel").grid(row=9, column=0, columnspan=3, sticky=tk.W, padx=10, pady=10)

        # Live Gamepad Feedback
        feedback_frame = ttk.LabelFrame(tab, text="État du Gamepad en temps réel")
        feedback_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Frame for axes
        self.axes_frame = ttk.Frame(feedback_frame)
        self.axes_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        ttk.Label(self.axes_frame, text="Axes:", style="Header.TLabel").pack(anchor=tk.W)

        # Frame for buttons
        self.buttons_frame = ttk.Frame(feedback_frame)
        self.buttons_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        ttk.Label(self.buttons_frame, text="Boutons:", style="Header.TLabel").pack(anchor=tk.W)

        # Initialize the feedback displays
        if self.joystick:
            self.update_axes_display()
            self.update_buttons_display()

    def create_calibration_tab(self):
        """Create the calibration tab for axes"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Calibration")

        # Header
        header = ttk.Frame(tab)
        header.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(header, text="Calibration des Axes", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(header, text="Ajustez les paramètres de calibration pour les axes").pack(anchor=tk.W)

        # Calibration Frame
        calibration_frame = ttk.LabelFrame(tab, text="Paramètres de Calibration")
        calibration_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create variables for calibration settings
        self.calibration_vars = {}
        self.calibration_vars["throttle_deadzone"] = DoubleVar(value=self.config["calibration"]["throttle_deadzone"])
        self.calibration_vars["steering_deadzone"] = DoubleVar(value=self.config["calibration"]["steering_deadzone"])
        self.calibration_vars["throttle_min"] = DoubleVar(value=self.config["calibration"]["throttle_min"])
        self.calibration_vars["throttle_max"] = DoubleVar(value=self.config["calibration"]["throttle_max"])
        self.calibration_vars["steering_min"] = DoubleVar(value=self.config["calibration"]["steering_min"])
        self.calibration_vars["steering_max"] = DoubleVar(value=self.config["calibration"]["steering_max"])
        self.calibration_vars["invert_throttle"] = IntVar(value=1 if self.config["calibration"]["invert_throttle"] else 0)
        self.calibration_vars["invert_steering"] = IntVar(value=1 if self.config["calibration"]["invert_steering"] else 0)

        # Throttle Calibration
        ttk.Label(calibration_frame, text="Accélérateur", style="Header.TLabel").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)

        ttk.Label(calibration_frame, text="Deadzone:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Scale(calibration_frame, from_=0.0, to=0.5, variable=self.calibration_vars["throttle_deadzone"],
                 orient=tk.HORIZONTAL, length=200).grid(row=1, column=1, padx=10, pady=2)
        ttk.Label(calibration_frame, textvariable=self.calibration_vars["throttle_deadzone"]).grid(row=1, column=2, padx=10, pady=2)

        ttk.Label(calibration_frame, text="Valeur Min:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Scale(calibration_frame, from_=-1.0, to=0.0, variable=self.calibration_vars["throttle_min"],
                 orient=tk.HORIZONTAL, length=200).grid(row=2, column=1, padx=10, pady=2)
        ttk.Label(calibration_frame, textvariable=self.calibration_vars["throttle_min"]).grid(row=2, column=2, padx=10, pady=2)

        ttk.Label(calibration_frame, text="Valeur Max:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Scale(calibration_frame, from_=0.0, to=1.0, variable=self.calibration_vars["throttle_max"],
                 orient=tk.HORIZONTAL, length=200).grid(row=3, column=1, padx=10, pady=2)
        ttk.Label(calibration_frame, textvariable=self.calibration_vars["throttle_max"]).grid(row=3, column=2, padx=10, pady=2)

        ttk.Checkbutton(calibration_frame, text="Inverser l'accélérateur", variable=self.calibration_vars["invert_throttle"]).grid(
            row=4, column=0, columnspan=2, sticky=tk.W, padx=10, pady=2)

        # Steering Calibration
        ttk.Label(calibration_frame, text="Direction", style="Header.TLabel").grid(row=5, column=0, sticky=tk.W, padx=10, pady=10)

        ttk.Label(calibration_frame, text="Deadzone:").grid(row=6, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Scale(calibration_frame, from_=0.0, to=0.5, variable=self.calibration_vars["steering_deadzone"],
                 orient=tk.HORIZONTAL, length=200).grid(row=6, column=1, padx=10, pady=2)
        ttk.Label(calibration_frame, textvariable=self.calibration_vars["steering_deadzone"]).grid(row=6, column=2, padx=10, pady=2)

        ttk.Label(calibration_frame, text="Valeur Min:").grid(row=7, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Scale(calibration_frame, from_=-1.0, to=0.0, variable=self.calibration_vars["steering_min"],
                 orient=tk.HORIZONTAL, length=200).grid(row=7, column=1, padx=10, pady=2)
        ttk.Label(calibration_frame, textvariable=self.calibration_vars["steering_min"]).grid(row=7, column=2, padx=10, pady=2)

        ttk.Label(calibration_frame, text="Valeur Max:").grid(row=8, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Scale(calibration_frame, from_=0.0, to=1.0, variable=self.calibration_vars["steering_max"],
                 orient=tk.HORIZONTAL, length=200).grid(row=8, column=1, padx=10, pady=2)
        ttk.Label(calibration_frame, textvariable=self.calibration_vars["steering_max"]).grid(row=8, column=2, padx=10, pady=2)

        ttk.Checkbutton(calibration_frame, text="Inverser la direction", variable=self.calibration_vars["invert_steering"]).grid(
            row=9, column=0, columnspan=2, sticky=tk.W, padx=10, pady=2)

        # Calibration Buttons
        button_frame = ttk.Frame(calibration_frame)
        button_frame.grid(row=10, column=0, columnspan=3, pady=20)

        ttk.Button(button_frame, text="Calibrer Accélérateur",
                  command=lambda: self.run_axis_calibration("throttle")).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Calibrer Direction",
                  command=lambda: self.run_axis_calibration("steering")).pack(side=tk.LEFT, padx=10)

        # Calibration status
        self.calibration_status = StringVar(value="Utilisez les boutons ci-dessus pour calibrer les axes")
        ttk.Label(calibration_frame, textvariable=self.calibration_status, style="Info.TLabel").grid(
            row=11, column=0, columnspan=3, pady=10)

    def create_performance_tab(self):
        """Create the performance settings tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Performance")

        # Header
        header = ttk.Frame(tab)
        header.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(header, text="Paramètres de Performance", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(header, text="Ajustez les paramètres de performance pour le contrôle du véhicule").pack(anchor=tk.W)

        # Performance Frame
        performance_frame = ttk.LabelFrame(tab, text="Paramètres")
        performance_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create variables for performance settings
        self.performance_vars = {}
        self.performance_vars["max_duty_cycle"] = DoubleVar(value=self.config["performance"]["max_duty_cycle"])
        self.performance_vars["max_rpm"] = IntVar(value=self.config["performance"]["max_rpm"])
        self.performance_vars["max_current"] = DoubleVar(value=self.config["performance"]["max_current"])
        self.performance_vars["control_mode"] = StringVar(value=self.config["performance"]["control_mode"])
        self.performance_vars["boost_multiplier"] = DoubleVar(value=self.config["performance"]["boost_multiplier"])
        self.performance_vars["cruise_increment"] = DoubleVar(value=self.config["performance"]["cruise_increment"])
        self.performance_vars["serial_port"] = StringVar(value=self.config["performance"].get("serial_port", "/dev/ttyACM0"))
        self.performance_vars["baud_rate"] = IntVar(value=self.config["performance"].get("baud_rate", 115200))

        # Max Duty Cycle
        ttk.Label(performance_frame, text="Duty Cycle Maximum:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Scale(performance_frame, from_=0.1, to=1.0, variable=self.performance_vars["max_duty_cycle"],
                 orient=tk.HORIZONTAL, length=200).grid(row=0, column=1, padx=10, pady=2)
        ttk.Label(performance_frame, textvariable=self.performance_vars["max_duty_cycle"]).grid(row=0, column=2, padx=10, pady=2)

        # Max RPM
        ttk.Label(performance_frame, text="RPM Maximum:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Scale(performance_frame, from_=1000, to=20000, variable=self.performance_vars["max_rpm"],
                 orient=tk.HORIZONTAL, length=200).grid(row=1, column=1, padx=10, pady=2)
        ttk.Label(performance_frame, textvariable=self.performance_vars["max_rpm"]).grid(row=1, column=2, padx=10, pady=2)

        # Max Current
        ttk.Label(performance_frame, text="Courant Maximum (A):").grid(row=2, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Scale(performance_frame, from_=1, to=50, variable=self.performance_vars["max_current"],
                 orient=tk.HORIZONTAL, length=200).grid(row=2, column=1, padx=10, pady=2)
        ttk.Label(performance_frame, textvariable=self.performance_vars["max_current"]).grid(row=2, column=2, padx=10, pady=2)

        # Control Mode
        ttk.Label(performance_frame, text="Mode de Contrôle:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=2)
        control_mode_combo = ttk.Combobox(performance_frame, textvariable=self.performance_vars["control_mode"],
                                         values=["duty_cycle", "rpm", "current"])
        control_mode_combo.grid(row=3, column=1, sticky=tk.W, padx=10, pady=2)

        # Boost Multiplier
        ttk.Label(performance_frame, text="Multiplicateur Boost:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Scale(performance_frame, from_=1.0, to=3.0, variable=self.performance_vars["boost_multiplier"],
                 orient=tk.HORIZONTAL, length=200).grid(row=4, column=1, padx=10, pady=2)
        ttk.Label(performance_frame, textvariable=self.performance_vars["boost_multiplier"]).grid(row=4, column=2, padx=10, pady=2)

        # Cruise Control Increment
        ttk.Label(performance_frame, text="Incrément Régulateur:").grid(row=5, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Scale(performance_frame, from_=0.01, to=0.2, variable=self.performance_vars["cruise_increment"],
                 orient=tk.HORIZONTAL, length=200).grid(row=5, column=1, padx=10, pady=2)
        ttk.Label(performance_frame, textvariable=self.performance_vars["cruise_increment"]).grid(row=5, column=2, padx=10, pady=2)

        # Serial Connection Settings
        ttk.Label(performance_frame, text="Paramètres de connexion", style="Header.TLabel").grid(
            row=6, column=0, sticky=tk.W, padx=10, pady=10)

        # Serial Port
        ttk.Label(performance_frame, text="Port Série:").grid(row=7, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Entry(performance_frame, textvariable=self.performance_vars["serial_port"]).grid(
            row=7, column=1, sticky=tk.W, padx=10, pady=2)

        # Baud Rate
        ttk.Label(performance_frame, text="Vitesse (Baud):").grid(row=8, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Combobox(performance_frame, textvariable=self.performance_vars["baud_rate"],
                    values=["9600", "19200", "38400", "57600", "115200", "230400"]).grid(
            row=8, column=1, sticky=tk.W, padx=10, pady=2)

    def create_test_tab(self):
        """Create the test tab to verify configuration"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Test")

        # Header
        header = ttk.Frame(tab)
        header.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(header, text="Test de Configuration", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(header, text="Testez votre configuration en temps réel").pack(anchor=tk.W)

        # Test Frame
        test_frame = ttk.LabelFrame(tab, text="Test en temps réel")
        test_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Throttle display
        throttle_frame = ttk.Frame(test_frame)
        throttle_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(throttle_frame, text="Accélérateur:", style="Header.TLabel").pack(side=tk.LEFT)
        self.throttle_value = DoubleVar(value=0.0)
        self.throttle_bar = ttk.Progressbar(throttle_frame, orient=tk.HORIZONTAL, length=400,
                                           mode='determinate', variable=self.throttle_value)
        self.throttle_bar.pack(side=tk.LEFT, padx=10)
        ttk.Label(throttle_frame, textvariable=self.throttle_value).pack(side=tk.LEFT)

        # Steering display
        steering_frame = ttk.Frame(test_frame)
        steering_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(steering_frame, text="Direction:", style="Header.TLabel").pack(side=tk.LEFT)
        self.steering_value = DoubleVar(value=0.0)
        self.steering_bar = ttk.Progressbar(steering_frame, orient=tk.HORIZONTAL, length=400,
                                           mode='determinate', variable=self.steering_value)
        self.steering_bar.pack(side=tk.LEFT, padx=10)
        ttk.Label(steering_frame, textvariable=self.steering_value).pack(side=tk.LEFT)

        # Button states display
        buttons_frame = ttk.LabelFrame(test_frame, text="État des Boutons")
        buttons_frame.pack(fill=tk.BOTH, padx=10, pady=10)

        self.button_states_display = {}

        # Emergency Stop
        emergency_frame = ttk.Frame(buttons_frame)
        emergency_frame.pack(fill=tk.X, pady=5)
        ttk.Label(emergency_frame, text="Arrêt d'urgence:").pack(side=tk.LEFT, padx=10)
        self.button_states_display["emergency"] = StringVar(value="Off")
        ttk.Label(emergency_frame, textvariable=self.button_states_display["emergency"]).pack(side=tk.LEFT)

        # Boost
        boost_frame = ttk.Frame(buttons_frame)
        boost_frame.pack(fill=tk.X, pady=5)
        ttk.Label(boost_frame, text="Boost:").pack(side=tk.LEFT, padx=10)
        self.button_states_display["boost"] = StringVar(value="Off")
        ttk.Label(boost_frame, textvariable=self.button_states_display["boost"]).pack(side=tk.LEFT)

        # Reverse
        reverse_frame = ttk.Frame(buttons_frame)
        reverse_frame.pack(fill=tk.X, pady=5)
        ttk.Label(reverse_frame, text="Marche arrière:").pack(side=tk.LEFT, padx=10)
        self.button_states_display["reverse"] = StringVar(value="Off")
        ttk.Label(reverse_frame, textvariable=self.button_states_display["reverse"]).pack(side=tk.LEFT)

        # Cruise Control
        cruise_frame = ttk.Frame(buttons_frame)
        cruise_frame.pack(fill=tk.X, pady=5)
        ttk.Label(cruise_frame, text="Régulateur de vitesse:").pack(side=tk.LEFT, padx=10)
        self.button_states_display["cruise"] = StringVar(value="Off")
        ttk.Label(cruise_frame, textvariable=self.button_states_display["cruise"]).pack(side=tk.LEFT)

        # Output Display
        output_frame = ttk.LabelFrame(test_frame, text="Sortie VESC")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.vesc_output = tk.Text(output_frame, height=8, width=70, wrap=tk.WORD)
        self.vesc_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.vesc_output.insert(tk.END, "La sortie VESC simulée sera affichée ici...\n")

    def start_listening(self, control_name):
        """Start listening for gamepad input to map a control"""
        if not self.joystick:
            messagebox.showerror("Erreur", "Aucun gamepad détecté ! Veuillez connecter un gamepad d'abord.")
            return

        self.listening_for = control_name
        type_control = "bouton" if "btn" in control_name else "axe"
        self.mapping_status.set(f"En attente d'input... Actionnez l'{type_control} pour '{control_name}'")

        # Initialize baseline for axis detection
        if "axis" in control_name:
            self.axis_baseline = []
            for i in range(self.joystick.get_numaxes()):
                self.axis_baseline.append(self.joystick.get_axis(i))

    def update_gamepad_status(self):
        """Update the gamepad status regularly"""
        # Try to reconnect gamepad if not connected
        if not self.joystick:
            self.connect_gamepad()

        # Process events and get current values
        if self.joystick:
            # Process pygame events
            pygame.event.pump()

            # Update axis and button displays if they exist
            if hasattr(self, 'axes_frame'):
                self.update_axes_display()
            if hasattr(self, 'buttons_frame'):
                self.update_buttons_display()

            # Handle listening for control mapping
            if self.listening_for:
                self.detect_input()

            # Update test display
            if self.notebook.index(self.notebook.select()) == 4:  # Test tab is selected
                self.update_test_display()

        # Schedule the next update
        self.root.after(50, self.update_gamepad_status)

    def update_axes_display(self):
        """Update the axes display in the mapping tab"""
        # Clear previous display
        for widget in self.axes_frame.winfo_children():
            if widget != self.axes_frame.winfo_children()[0]:  # Keep the header
                widget.destroy()

        # Display current axes values
        for i in range(self.joystick.get_numaxes()):
            value = self.joystick.get_axis(i)
            self.axis_values[i] = value
            frame = ttk.Frame(self.axes_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"Axe {i}:").pack(side=tk.LEFT, padx=5)
            ttk.Label(frame, text=f"{value:.2f}").pack(side=tk.LEFT, padx=5)

    def update_buttons_display(self):
        """Update the buttons display in the mapping tab"""
        # Clear previous display
        for widget in self.buttons_frame.winfo_children():
            if widget != self.buttons_frame.winfo_children()[0]:  # Keep the header
                widget.destroy()

        # Display current button states
        for i in range(self.joystick.get_numbuttons()):
            state = self.joystick.get_button(i)
            self.button_states[i] = state
            frame = ttk.Frame(self.buttons_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"Bouton {i}:").pack(side=tk.LEFT, padx=5)
            ttk.Label(frame, text="ON" if state else "off").pack(side=tk.LEFT, padx=5)

    def detect_input(self):
        """Detect gamepad input for mapping"""
        if not self.joystick or not self.listening_for:
            return

        if "btn" in self.listening_for:
            # Detect button press
            for i in range(self.joystick.get_numbuttons()):
                if self.joystick.get_button(i):
                    self.detected_input = i
                    self.apply_mapping()
                    return
        else:
            # Detect significant axis movement
            for i in range(self.joystick.get_numaxes()):
                current = self.joystick.get_axis(i)
                if abs(current - self.axis_baseline[i]) > 0.5:
                    self.detected_input = i
                    self.apply_mapping()
                    return

    def apply_mapping(self):
        """Apply the detected input to the mapping"""
        if not self.detected_input is None:
            # Update the config and the display
            if "btn" in self.listening_for:
                self.config["controls"][self.listening_for] = self.detected_input
            else:
                self.config["controls"][self.listening_for] = self.detected_input

            # Update mapping var
            self.mapping_vars[self.listening_for].set(self.detected_input)

            # Reset
            self.mapping_status.set(f"'{self.listening_for}' mappé à {'bouton' if 'btn' in self.listening_for else 'axe'} {self.detected_input}")
            self.listening_for = None
            self.detected_input = None

    def update_test_display(self):
        """Update the test display tab"""
        if not self.joystick:
            return

        # Get control values
        throttle = self.config_manager.get_control_value("throttle")
        steering = self.config_manager.get_control_value("steering")

        # Update progress bars (scale from -1,1 to 0,100)
        self.throttle_value.set((throttle + 1) * 50)
        self.steering_value.set((steering + 1) * 50)

        # Update button states
        self.button_states_display["emergency"].set("ON" if self.config_manager.is_button_pressed("emergency_stop") else "Off")
        self.button_states_display["boost"].set("ON" if self.config_manager.is_button_pressed("boost") else "Off")
        self.button_states_display["reverse"].set("ON" if self.config_manager.is_button_pressed("reverse") else "Off")
        self.button_states_display["cruise"].set("ON" if self.config_manager.is_button_pressed("cruise_toggle") else "Off")

        # Simulate VESC output
        if throttle != 0 or steering != 0:
            control_mode = self.config["performance"]["control_mode"]
            max_val = self.config["performance"]["max_duty_cycle"] if control_mode == "duty_cycle" else \
                    self.config["performance"]["max_rpm"] if control_mode == "rpm" else \
                    self.config["performance"]["max_current"]

            self.vesc_output.insert(tk.END, f"Envoi {control_mode}: Throttle={throttle:.2f}, Steering={steering:.2f}, "
                                           f"Valeur={throttle * max_val:.2f}\n")
            self.vesc_output.see(tk.END)

            # Limit the number of lines in the output
            lines = self.vesc_output.get("1.0", tk.END).split("\n")
            if len(lines) > 50:
                self.vesc_output.delete("1.0", f"{len(lines)-50}.0")

    def run_axis_calibration(self, axis_name):
        """Run an interactive calibration for an axis"""
        if not self.joystick:
            messagebox.showerror("Erreur", "Aucun gamepad détecté ! Veuillez connecter un gamepad d'abord.")
            return

        # Determine which axis to calibrate
        axis_index = self.config["controls"][f"{axis_name}_axis"]

        # Open a calibration dialog
        calibration_window = tk.Toplevel(self.root)
        calibration_window.title(f"Calibration de l'axe {axis_name}")
        calibration_window.geometry("400x300")
        calibration_window.transient(self.root)
        calibration_window.grab_set()

        # Calibration instructions
        ttk.Label(calibration_window, text=f"Calibration de l'{axis_name}", style="Title.TLabel").pack(pady=10)
        ttk.Label(calibration_window, text=f"1. Déplacez l'axe jusqu'à sa position minimale puis cliquez sur 'Définir Min'").pack(anchor=tk.W, padx=20, pady=5)
        ttk.Label(calibration_window, text=f"2. Déplacez l'axe jusqu'à sa position maximale puis cliquez sur 'Définir Max'").pack(anchor=tk.W, padx=20, pady=5)
        ttk.Label(calibration_window, text=f"3. Relâchez l'axe en position neutre et ajustez la deadzone si nécessaire").pack(anchor=tk.W, padx=20, pady=5)

        # Current value display
        value_frame = ttk.Frame(calibration_window)
        value_frame.pack(pady=10)
        ttk.Label(value_frame, text="Valeur actuelle:").pack(side=tk.LEFT)
        current_value = StringVar(value="0.00")
        ttk.Label(value_frame, textvariable=current_value).pack(side=tk.LEFT, padx=10)

        # Min/Max calibration buttons
        button_frame = ttk.Frame(calibration_window)
        button_frame.pack(pady=10)

        min_value = DoubleVar()
        max_value = DoubleVar()

        def set_min():
            min_value.set(self.joystick.get_axis(axis_index))
            min_btn.config(text=f"Min: {min_value.get():.2f}")

        def set_max():
            max_value.set(self.joystick.get_axis(axis_index))
            max_btn.config(text=f"Max: {max_value.get():.2f}")

        min_btn = ttk.Button(button_frame, text="Définir Min", command=set_min)
        min_btn.pack(side=tk.LEFT, padx=10)

        max_btn = ttk.Button(button_frame, text="Définir Max", command=set_max)
        max_btn.pack(side=tk.LEFT, padx=10)

        # Inversion option
        invert_var = IntVar(value=1 if self.config["calibration"][f"invert_{axis_name}"] else 0)
        ttk.Checkbutton(calibration_window, text=f"Inverser {axis_name}", variable=invert_var).pack(pady=5)

        # Deadzone slider
        deadzone_frame = ttk.Frame(calibration_window)
        deadzone_frame.pack(pady=10, fill=tk.X, padx=20)

        ttk.Label(deadzone_frame, text="Deadzone:").pack(side=tk.LEFT)
        deadzone_var = DoubleVar(value=self.config["calibration"][f"{axis_name}_deadzone"])
        deadzone_scale = ttk.Scale(deadzone_frame, from_=0.0, to=0.5, variable=deadzone_var, orient=tk.HORIZONTAL)
        deadzone_scale.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        ttk.Label(deadzone_frame, textvariable=deadzone_var).pack(side=tk.LEFT, padx=5)

        # Save and cancel buttons
        action_frame = ttk.Frame(calibration_window)
        action_frame.pack(pady=20, fill=tk.X, padx=20)

        def save_calibration():
            # Update config with new calibration values
            self.config["calibration"][f"{axis_name}_min"] = min_value.get()
            self.config["calibration"][f"{axis_name}_max"] = max_value.get()
            self.config["calibration"][f"{axis_name}_deadzone"] = deadzone_var.get()
            self.config["calibration"][f"invert_{axis_name}"] = bool(invert_var.get())

            # Update UI variables
            self.calibration_vars[f"{axis_name}_min"].set(min_value.get())
            self.calibration_vars[f"{axis_name}_max"].set(max_value.get())
            self.calibration_vars[f"{axis_name}_deadzone"].set(deadzone_var.get())
            self.calibration_vars[f"invert_{axis_name}"].set(invert_var.get())

            self.calibration_status.set(f"Calibration de {axis_name} terminée avec succès")
            calibration_window.destroy()

        ttk.Button(action_frame, text="Annuler", command=calibration_window.destroy).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="Enregistrer", command=save_calibration).pack(side=tk.RIGHT, padx=10)

        # Function to update current value display
        def update_display():
            if calibration_window.winfo_exists():
                current_value.set(f"{self.joystick.get_axis(axis_index):.2f}")
                calibration_window.after(50, update_display)

        # Start the update loop
        update_display()

    def update_gamepad_info(self):
        """Update the gamepad information display"""
        if not self.joystick:
            self.gamepad_info_text.config(state=tk.NORMAL)
            self.gamepad_info_text.delete(1.0, tk.END)
            self.gamepad_info_text.insert(tk.END, "Aucun gamepad connecté. Veuillez connecter un gamepad pour afficher ses informations.")
            self.gamepad_info_text.config(state=tk.DISABLED)
            return

        # Get gamepad info
        name = self.joystick.get_name()
        num_axes = self.joystick.get_numaxes()
        num_buttons = self.joystick.get_numbuttons()
        num_hats = self.joystick.get_numhats()

        # Format info
        info = f"Nom: {name}\n"
        info += f"Nombre d'axes: {num_axes}\n"
        info += f"Nombre de boutons: {num_buttons}\n"
        info += f"Nombre de chapeaux: {num_hats}\n\n"

        # Add current mapping info
        info += "Mapping actuel:\n"
        info += f"Accélérateur: Axe {self.config['controls']['throttle_axis']}\n"
        info += f"Direction: Axe {self.config['controls']['steering_axis']}\n"
        info += f"Frein: Axe {self.config['controls']['brake_axis']}\n"
        info += f"Arrêt d'urgence: Bouton {self.config['controls']['emergency_stop_btn']}\n"
        info += f"Boost: Bouton {self.config['controls']['boost_btn']}\n"
        info += f"Marche arrière: Bouton {self.config['controls']['reverse_btn']}\n"
        info += f"Régulateur de vitesse: Bouton {self.config['controls']['cruise_toggle_btn']}\n"

        # Update text widget
        self.gamepad_info_text.config(state=tk.NORMAL)
        self.gamepad_info_text.delete(1.0, tk.END)
        self.gamepad_info_text.insert(tk.END, info)
        self.gamepad_info_text.config(state=tk.DISABLED)

    def refresh_gamepad(self):
        """Refresh the gamepad connection"""
        if self.joystick:
            self.joystick.quit()
            self.joystick = None

        pygame.joystick.quit()
        pygame.joystick.init()

        if self.connect_gamepad():
            self.status_text.set(f"Gamepad actualisé: {self.joystick.get_name()}")
            self.update_gamepad_info()
        else:
            self.status_text.set("Aucun gamepad détecté. Veuillez connecter un gamepad.")

    def save_config(self):
        """Save the current configuration"""
        # Update config from UI variables

        # Update control mappings
        for key, var in self.mapping_vars.items():
            if key in self.config["controls"]:
                self.config["controls"][key] = var.get()

        # Update calibration settings if they exist
        if hasattr(self, 'calibration_vars'):
            for key, var in self.calibration_vars.items():
                if key in self.config["calibration"]:
                    if key.startswith("invert_"):
                        self.config["calibration"][key] = bool(var.get())
                    else:
                        self.config["calibration"][key] = var.get()

        # Update performance settings if they exist
        if hasattr(self, 'performance_vars'):
            for key, var in self.performance_vars.items():
                if key in self.config["performance"] or key in ["serial_port", "baud_rate"]:
                    self.config["performance"][key] = var.get()

        # Save configuration
        result = self.config_manager.save_config()
        if result:
            messagebox.showinfo("Succès", "Configuration enregistrée avec succès!")
            self.status_text.set("Configuration enregistrée")
        else:
            messagebox.showerror("Erreur", "Impossible d'enregistrer la configuration")

    def restore_defaults(self):
        """Restore default configuration"""
        if messagebox.askyesno("Confirmer", "Êtes-vous sûr de vouloir restaurer la configuration par défaut ?"):
            self.config = DEFAULT_CONFIG.copy()
            self.config_manager.config = self.config

            # Update UI variables
            self.setup_ui_variables()

            self.status_text.set("Configuration par défaut restaurée")

    def setup_ui_variables(self):
        """Update all UI variables from the current config"""
        # Update mapping variables
        for key in self.mapping_vars:
            if key in self.config["controls"]:
                self.mapping_vars[key].set(self.config["controls"][key])

        # Update calibration variables
        if hasattr(self, 'calibration_vars'):
            for key in self.calibration_vars:
                if key in self.config["calibration"]:
                    if key.startswith("invert_"):
                        self.calibration_vars[key].set(1 if self.config["calibration"][key] else 0)
                    else:
                        self.calibration_vars[key].set(self.config["calibration"][key])

        # Update performance variables
        if hasattr(self, 'performance_vars'):
            for key in self.performance_vars:
                if key in self.config["performance"]:
                    self.performance_vars[key].set(self.config["performance"][key])

        # Update gamepad info
        self.update_gamepad_info()


if __name__ == "__main__":
    root = tk.Tk()
    app = GamepadGUI(root)
    root.mainloop()

    # Ensure pygame quits properly
    pygame.quit()
