"""
robocar_server.py

Serveur principal pour le contrôle du Robocar via réseau.
Reçoit les commandes UDP et les applique au VESC.
"""

import socket
import time
import threading
import logging
import yaml
from datetime import datetime
from typing import Optional, Dict, Any
import queue

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.robocar_base import Robocar, ROBOCAR_CONFIG
from core.protocol import (
    decode_message,
    extract_control_data,
    extract_commands,
    get_message_source,
    MessageType,
    CommandType
)
from server.telemetry_publisher import TelemetryPublisher
from server.watchdog import Watchdog


class RobocarServer:
    """
    Serveur de contrôle Robocar.

    Gère:
    - Réception commandes UDP
    - Application au VESC via Robocar
    - Publication télémétrie
    - Watchdog de sécurité
    - Logging des sessions
    """

    def __init__(self, config_file: str = "config/server_config.yaml"):
        """
        Initialise le serveur.

        Args:
            config_file: Chemin vers fichier de configuration
        """
        # Charger configuration
        self.config = self._load_config(config_file)

        # Configuration serveur
        server_cfg = self.config.get('server', {})
        self.control_port = server_cfg.get('control_port', 5000)
        self.telemetry_port = server_cfg.get('telemetry_port', 5001)
        self.bind_address = server_cfg.get('bind_address', '0.0.0.0')
        self.telemetry_rate = server_cfg.get('telemetry_rate_hz', 20)

        # Configuration sécurité
        safety_cfg = self.config.get('safety', {})
        self.watchdog_timeout = safety_cfg.get('watchdog_timeout_ms', 500) / 1000.0
        self.emergency_timeout = safety_cfg.get('emergency_stop_timeout_ms', 1000) / 1000.0

        # Configuration robocar
        robocar_cfg = self.config.get('robocar', ROBOCAR_CONFIG)

        # Filtrer seulement les paramètres acceptés par Robocar.__init__
        robocar_init_params = {
            'port': robocar_cfg.get('port', '/dev/ttyACM0'),
            'baudrate': robocar_cfg.get('baudrate', 115200),
            'throttle_max': robocar_cfg.get('throttle_max', 0.1),
            'steering_left': robocar_cfg.get('steering_left', 0.0),
            'steering_right': robocar_cfg.get('steering_right', 1.0),
            'steering_center': robocar_cfg.get('steering_center', 0.5),
            'kick_start_duty': robocar_cfg.get('kick_start_duty', 0.25),
            'kick_start_duration_ms': robocar_cfg.get('kick_start_duration_ms', 150),
            'dead_zone_threshold': robocar_cfg.get('dead_zone_threshold', 0.05),
        }

        # Initialiser Robocar
        self.robocar = Robocar(**robocar_init_params)

        # Appliquer configuration supplémentaire après initialisation
        if 'throttle_smoothing_alpha' in robocar_cfg and 'throttle_max_change' in robocar_cfg:
            self.robocar.set_throttle_smoothing(
                alpha=robocar_cfg['throttle_smoothing_alpha'],
                max_change=robocar_cfg['throttle_max_change']
            )

        # Socket de contrôle
        self.control_socket: Optional[socket.socket] = None

        # État
        self.running = False
        self.active_client_id: Optional[str] = None
        self.command_queue = queue.Queue()

        # Modules
        self.telemetry_publisher: Optional[TelemetryPublisher] = None
        self.watchdog: Optional[Watchdog] = None

        # Threads
        self.control_thread: Optional[threading.Thread] = None
        self.command_processor_thread: Optional[threading.Thread] = None

        # Statistiques
        self.start_time = 0
        self.messages_received = 0
        self.messages_processed = 0
        self.errors_count = 0

        # Logging
        self._setup_logging()

        self.logger.info("=== Robocar Server Initialisé ===")
        self.logger.info(f"Port contrôle: {self.control_port}")
        self.logger.info(f"Port télémétrie: {self.telemetry_port}")

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Charge la configuration depuis un fichier YAML."""
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                print(f"✅ Configuration chargée depuis {config_file}")
                return config
        except Exception as e:
            print(f"⚠️  Erreur chargement config: {e}")
            print("Utilisation configuration par défaut")
            return {
                'server': {},
                'safety': {},
                'robocar': ROBOCAR_CONFIG,
                'logging': {}
            }

    def _setup_logging(self):
        """Configure le système de logging."""
        log_cfg = self.config.get('logging', {})

        if not log_cfg.get('enable', True):
            self.logger = logging.getLogger('robocar_server')
            self.logger.addHandler(logging.NullHandler())
            return

        # Créer logger
        self.logger = logging.getLogger('robocar_server')
        level = getattr(logging, log_cfg.get('level', 'INFO'))
        self.logger.setLevel(level)

        # Handler console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # Handler fichier
        log_file = log_cfg.get('log_file', 'logs/server_{date}.log')
        log_file = log_file.format(date=datetime.now().strftime('%Y%m%d'))

        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_format = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
            self.logger.info(f"Logs enregistrés dans {log_file}")
        except Exception as e:
            self.logger.warning(f"Impossible de créer fichier log: {e}")

        # Session log (JSON lines pour replay)
        if log_cfg.get('log_commands', True):
            session_file = log_cfg.get('session_log_file', 'logs/session_{date}.jsonl')
            session_file = session_file.format(date=datetime.now().strftime('%Y%m%d_%H%M%S'))
            try:
                os.makedirs(os.path.dirname(session_file), exist_ok=True)
                self.session_log = open(session_file, 'a')
                self.logger.info(f"Session log: {session_file}")
            except Exception as e:
                self.logger.warning(f"Impossible de créer session log: {e}")
                self.session_log = None
        else:
            self.session_log = None

    def start(self) -> bool:
        """
        Démarre le serveur.

        Returns:
            True si démarrage réussi
        """
        self.logger.info("Démarrage du serveur...")

        # Connecter au VESC
        if not self.robocar.connect():
            self.logger.error("❌ Impossible de se connecter au VESC")
            return False

        # Créer socket de contrôle
        try:
            self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.control_socket.bind((self.bind_address, self.control_port))
            self.control_socket.settimeout(1.0)
            self.logger.info(f"✅ Socket contrôle: {self.bind_address}:{self.control_port}")
        except Exception as e:
            self.logger.error(f"❌ Erreur création socket: {e}")
            self.robocar.disconnect()
            return False

        # Initialiser modules
        self.telemetry_publisher = TelemetryPublisher(
            self.robocar,
            port=self.telemetry_port,
            publish_rate_hz=self.telemetry_rate
        )

        self.watchdog = Watchdog(
            self.robocar,
            timeout=self.watchdog_timeout,
            stop_timeout=self.emergency_timeout
        )

        # Démarrer
        self.running = True
        self.start_time = time.time()

        # Démarrer threads
        self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self.control_thread.start()

        self.command_processor_thread = threading.Thread(target=self._command_processor, daemon=True)
        self.command_processor_thread.start()

        # Démarrer modules
        self.telemetry_publisher.start()
        self.watchdog.start()

        self.logger.info("✅ Serveur démarré avec succès")
        self.logger.info("En attente de commandes...")

        return True

    def stop(self):
        """Arrête le serveur proprement."""
        self.logger.info("Arrêt du serveur...")
        self.running = False

        # Arrêter modules
        if self.watchdog:
            self.watchdog.stop()
        if self.telemetry_publisher:
            self.telemetry_publisher.stop()

        # Fermer socket
        if self.control_socket:
            self.control_socket.close()

        # Attendre threads
        if self.control_thread and self.control_thread.is_alive():
            self.control_thread.join(timeout=2.0)
        if self.command_processor_thread and self.command_processor_thread.is_alive():
            self.command_processor_thread.join(timeout=2.0)

        # Déconnecter robocar
        self.robocar.disconnect()

        # Fermer session log
        if self.session_log:
            self.session_log.close()

        # Statistiques finales
        uptime = time.time() - self.start_time
        self.logger.info("=== Statistiques ===")
        self.logger.info(f"Uptime: {uptime:.1f}s")
        self.logger.info(f"Messages reçus: {self.messages_received}")
        self.logger.info(f"Messages traités: {self.messages_processed}")
        self.logger.info(f"Erreurs: {self.errors_count}")

        self.logger.info("Serveur arrêté")

    def _control_loop(self):
        """Thread de réception des commandes UDP."""
        self.logger.info("Thread de contrôle démarré")

        while self.running:
            try:
                # Recevoir message
                data, client_addr = self.control_socket.recvfrom(4096)
                message_str = data.decode('utf-8')

                self.messages_received += 1

                # Décoder message
                message, error = decode_message(message_str)
                if error:
                    self.logger.warning(f"Message invalide de {client_addr}: {error}")
                    self.errors_count += 1
                    continue

                # Ajouter à la queue de traitement
                self.command_queue.put((message, client_addr))

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"Erreur réception: {e}")
                    self.errors_count += 1

    def _command_processor(self):
        """Thread de traitement des commandes."""
        self.logger.info("Thread de traitement démarré")

        while self.running:
            try:
                # Récupérer commande de la queue
                try:
                    message, client_addr = self.command_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Traiter selon le type
                msg_type = message.get('type')

                if msg_type == MessageType.CONTROL:
                    self._handle_control_message(message, client_addr)
                elif msg_type == MessageType.HEARTBEAT:
                    self._handle_heartbeat(message, client_addr)
                else:
                    self.logger.debug(f"Type de message ignoré: {msg_type}")

                self.messages_processed += 1

            except Exception as e:
                self.logger.error(f"Erreur traitement: {e}")
                self.errors_count += 1

    def _handle_control_message(self, message: Dict[str, Any], client_addr):
        """Traite un message de contrôle."""
        source = get_message_source(message)

        # Mettre à jour client actif
        if self.active_client_id != source:
            self.logger.info(f"Nouveau client actif: {source} ({client_addr})")
            self.active_client_id = source
            if self.telemetry_publisher:
                self.telemetry_publisher.set_active_client(source)

        # Mettre à jour watchdog
        self.watchdog.update_last_command()

        # Extraire données de contrôle
        control_data = extract_control_data(message)
        if control_data:
            throttle = control_data.get('throttle', 0.0)
            steering = control_data.get('steering', 0.0)
            throttle_max = control_data.get('throttle_max')

            # Appliquer au robocar
            self.robocar.set_throttle(throttle)
            self.robocar.set_steering(steering)

            if throttle_max is not None:
                self.robocar.throttle_max_power = throttle_max

            # Logger (si configuré)
            if self.session_log:
                import json
                log_entry = {
                    'timestamp': time.time(),
                    'source': source,
                    'throttle': throttle,
                    'steering': steering
                }
                self.session_log.write(json.dumps(log_entry) + '\n')
                self.session_log.flush()

        # Traiter commandes ponctuelles
        commands = extract_commands(message)
        for cmd in commands:
            self._execute_command(cmd)

    def _handle_heartbeat(self, message: Dict[str, Any], client_addr):
        """Traite un heartbeat."""
        source = get_message_source(message)
        # Mettre à jour watchdog même pour heartbeat
        self.watchdog.update_last_command()
        self.logger.debug(f"Heartbeat de {source}")

    def _execute_command(self, command: str):
        """Exécute une commande ponctuelle."""
        try:
            if command == CommandType.HORN:
                self.robocar.horn()
            elif command == CommandType.SOUND_EPITECH:
                self.robocar.play_sound("assets/EpitechPassion.wav")
            elif command == CommandType.SOUND_SATELISATION:
                self.robocar.play_sound("assets/Satelisation.wav")
            elif command == CommandType.SOUND_PETER:
                self.robocar.play_sound("assets/Peter.wav")
            elif command == CommandType.SOUND_POLIZIA:
                self.robocar.play_sound("assets/Polizia.wav")
            elif command == CommandType.INCREASE_SPEED:
                self.robocar.incr_throttle_max()
            elif command == CommandType.DECREASE_SPEED:
                self.robocar.decr_throttle_max()
            elif command == CommandType.EMERGENCY_STOP:
                self.robocar.emergency_stop()
                self.logger.warning("⚠️  ARRÊT D'URGENCE déclenché par commande")
            else:
                self.logger.warning(f"Commande inconnue: {command}")
        except Exception as e:
            self.logger.error(f"Erreur exécution commande '{command}': {e}")

    def get_status(self) -> Dict[str, Any]:
        """Retourne l'état du serveur."""
        return {
            'running': self.running,
            'uptime': time.time() - self.start_time if self.start_time > 0 else 0,
            'active_client': self.active_client_id,
            'messages_received': self.messages_received,
            'messages_processed': self.messages_processed,
            'errors': self.errors_count,
            'watchdog_status': self.watchdog.get_status() if self.watchdog else None
        }


# --- MAIN ---
def main():
    """Point d'entrée principal."""
    import argparse
    import signal

    parser = argparse.ArgumentParser(description="Robocar Server - Contrôle via réseau")
    parser.add_argument(
        '--config',
        default='config/server_config.yaml',
        help='Fichier de configuration YAML'
    )
    args = parser.parse_args()

    # Créer serveur
    server = RobocarServer(config_file=args.config)

    # Handler pour arrêt propre
    def signal_handler(sig, frame):
        print("\n\n🛑 Interruption détectée")
        server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Démarrer
    if server.start():
        try:
            # Rester actif
            while server.running:
                time.sleep(1)

                # Afficher statut périodiquement
                if int(time.time()) % 30 == 0:  # Toutes les 30s
                    status = server.get_status()
                    print(f"\n📊 Status: uptime={status['uptime']:.0f}s, "
                          f"msgs={status['messages_processed']}, "
                          f"client={status['active_client'] or 'none'}")

        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé")

    server.stop()


if __name__ == "__main__":
    main()
