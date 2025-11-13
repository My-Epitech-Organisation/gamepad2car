"""
base_client.py

Classe abstraite pour tous les clients Robocar.
Fournit les fonctionnalités de base de connexion réseau et communication.
"""

import socket
import time
import threading
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable
import yaml

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.protocol import (
    encode_control_message,
    decode_message,
    create_heartbeat_message,
    extract_control_data,
    MessageType
)


class BaseClient(ABC):
    """
    Classe abstraite pour les clients Robocar.
    
    Gère:
    - Connexion UDP au serveur
    - Envoi de commandes de contrôle
    - Réception de télémétrie
    - Heartbeat automatique
    - Reconnexion automatique
    """
    
    def __init__(
        self,
        client_id: str,
        server_ip: str = "127.0.0.1",
        control_port: int = 5000,
        telemetry_port: int = 5001,
        config_file: Optional[str] = None
    ):
        """
        Initialise le client.
        
        Args:
            client_id: Identifiant unique du client
            server_ip: Adresse IP du serveur
            control_port: Port d'envoi des commandes
            telemetry_port: Port de réception télémétrie
            config_file: Chemin vers fichier config YAML (optionnel)
        """
        self.client_id = client_id
        self.server_ip = server_ip
        self.control_port = control_port
        self.telemetry_port = telemetry_port
        
        # Charger config si fournie
        if config_file:
            self._load_config(config_file)
        
        # Sockets UDP
        self.control_socket = None
        self.telemetry_socket = None
        
        # État
        self.connected = False
        self.running = False
        self.sequence_number = 0
        self.last_telemetry = None
        self.last_telemetry_time = 0
        
        # Threads
        self.telemetry_thread = None
        self.heartbeat_thread = None
        
        # Callbacks
        self.telemetry_callback = None
        
        # Configuration
        self.heartbeat_interval = 0.1  # 100ms
        self.reconnect_timeout = 5.0
        self.request_timeout = 2.0
        
        print(f"[{self.client_id}] Client initialisé")
    
    def _load_config(self, config_file: str):
        """Charge la configuration depuis un fichier YAML."""
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                client_config = config.get('client', {})
                
                self.server_ip = client_config.get('server_ip', self.server_ip)
                self.control_port = client_config.get('control_port', self.control_port)
                self.telemetry_port = client_config.get('telemetry_port', self.telemetry_port)
                self.heartbeat_interval = client_config.get('heartbeat_interval_ms', 100) / 1000.0
                self.reconnect_timeout = client_config.get('reconnect_timeout_s', 5.0)
                self.request_timeout = client_config.get('request_timeout_s', 2.0)
                
                print(f"[{self.client_id}] Configuration chargée depuis {config_file}")
        except Exception as e:
            print(f"[{self.client_id}] ⚠️  Erreur chargement config: {e}")
    
    def connect(self) -> bool:
        """
        Établit la connexion avec le serveur.
        
        Returns:
            True si connexion réussie
        """
        try:
            # Socket pour envoyer commandes
            self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.control_socket.settimeout(self.request_timeout)
            
            # Socket pour recevoir télémétrie (broadcast)
            self.telemetry_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.telemetry_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.telemetry_socket.bind(('', self.telemetry_port))
            self.telemetry_socket.settimeout(1.0)
            
            self.connected = True
            self.running = True
            
            # Démarrer threads
            self.telemetry_thread = threading.Thread(target=self._telemetry_loop, daemon=True)
            self.telemetry_thread.start()
            
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()
            
            print(f"[{self.client_id}] ✅ Connecté au serveur {self.server_ip}:{self.control_port}")
            return True
            
        except Exception as e:
            print(f"[{self.client_id}] ❌ Erreur de connexion: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Ferme la connexion proprement."""
        print(f"[{self.client_id}] Déconnexion...")
        self.running = False
        self.connected = False
        
        # Envoyer une dernière commande d'arrêt
        try:
            self.send_control(throttle=0.0, steering=0.0)
        except:
            pass
        
        # Fermer sockets
        if self.control_socket:
            self.control_socket.close()
        if self.telemetry_socket:
            self.telemetry_socket.close()
        
        # Attendre fin des threads
        if self.telemetry_thread and self.telemetry_thread.is_alive():
            self.telemetry_thread.join(timeout=1.0)
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=1.0)
        
        print(f"[{self.client_id}] Déconnecté")
    
    def send_control(
        self,
        throttle: float,
        steering: float,
        throttle_max: Optional[float] = None,
        commands: Optional[list] = None
    ) -> bool:
        """
        Envoie une commande de contrôle au serveur.
        
        Args:
            throttle: Puissance moteur (-1.0 à 1.0)
            steering: Direction (-1.0 à 1.0)
            throttle_max: Puissance max optionnelle
            commands: Liste de commandes ponctuelles
            
        Returns:
            True si envoi réussi
        """
        if not self.connected:
            return False
        
        try:
            self.sequence_number += 1
            message = encode_control_message(
                source=self.client_id,
                throttle=throttle,
                steering=steering,
                throttle_max=throttle_max,
                commands=commands or [],
                sequence=self.sequence_number
            )
            
            self.control_socket.sendto(
                message.encode('utf-8'),
                (self.server_ip, self.control_port)
            )
            return True
            
        except Exception as e:
            print(f"[{self.client_id}] ❌ Erreur envoi: {e}")
            return False
    
    def _send_heartbeat(self):
        """Envoie un heartbeat au serveur."""
        if not self.connected:
            return
        
        try:
            self.sequence_number += 1
            message = create_heartbeat_message(
                source=self.client_id,
                sequence=self.sequence_number
            )
            
            self.control_socket.sendto(
                message.encode('utf-8'),
                (self.server_ip, self.control_port)
            )
            
        except Exception as e:
            # Ne pas afficher d'erreur pour heartbeat (trop verbeux)
            pass
    
    def _heartbeat_loop(self):
        """Thread qui envoie des heartbeats réguliers."""
        while self.running:
            self._send_heartbeat()
            time.sleep(self.heartbeat_interval)
    
    def _telemetry_loop(self):
        """Thread qui reçoit la télémétrie du serveur."""
        while self.running:
            try:
                data, addr = self.telemetry_socket.recvfrom(4096)
                message_str = data.decode('utf-8')
                
                message, error = decode_message(message_str)
                if error:
                    continue
                
                if message.get('type') == MessageType.TELEMETRY:
                    self.last_telemetry = message.get('data', {})
                    self.last_telemetry_time = time.time()
                    
                    # Appeler callback si défini
                    if self.telemetry_callback:
                        self.telemetry_callback(self.last_telemetry)
                        
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:  # Ne log que si on devrait être actif
                    print(f"[{self.client_id}] Erreur réception télémétrie: {e}")
    
    def set_telemetry_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Définit une fonction callback pour la télémétrie.
        
        Args:
            callback: Fonction appelée à chaque réception de télémétrie
                      Signature: callback(telemetry_data: Dict)
        """
        self.telemetry_callback = callback
    
    def get_last_telemetry(self) -> Optional[Dict[str, Any]]:
        """Retourne la dernière télémétrie reçue."""
        return self.last_telemetry
    
    def get_telemetry_age(self) -> float:
        """Retourne le temps depuis la dernière télémétrie (en secondes)."""
        if self.last_telemetry_time == 0:
            return float('inf')
        return time.time() - self.last_telemetry_time
    
    def is_telemetry_fresh(self, max_age: float = 1.0) -> bool:
        """Vérifie si la télémétrie est récente."""
        return self.get_telemetry_age() < max_age
    
    @abstractmethod
    def run(self):
        """
        Boucle principale du client (à implémenter dans les sous-classes).
        
        Cette méthode doit:
        1. Lire les entrées (gamepad, clavier, etc.)
        2. Appeler send_control() avec les valeurs appropriées
        3. Gérer la sortie propre
        """
        pass
    
    @abstractmethod
    def get_control_input(self) -> Dict[str, float]:
        """
        Retourne les valeurs de contrôle actuelles (à implémenter).
        
        Returns:
            Dict avec au minimum 'throttle' et 'steering'
        """
        pass


# --- TEST SIMPLE ---
if __name__ == "__main__":
    class TestClient(BaseClient):
        """Client de test simple."""
        
        def get_control_input(self):
            return {'throttle': 0.0, 'steering': 0.0}
        
        def run(self):
            print(f"[{self.client_id}] Test - Envoi de quelques commandes...")
            
            # Envoi de commandes de test
            for i in range(5):
                throttle = 0.3 if i < 3 else 0.0
                steering = 0.0
                
                self.send_control(throttle, steering)
                print(f"  Envoyé: throttle={throttle}, steering={steering}")
                
                time.sleep(0.5)
                
                # Afficher télémétrie si disponible
                if self.last_telemetry:
                    print(f"  Reçu: {self.last_telemetry}")
            
            print(f"[{self.client_id}] Test terminé")
    
    # Lancer le test
    print("=== Test BaseClient ===\n")
    client = TestClient(client_id="test_001", server_ip="127.0.0.1")
    
    if client.connect():
        try:
            client.run()
        except KeyboardInterrupt:
            print("\nInterrompu par l'utilisateur")
        finally:
            client.disconnect()
    else:
        print("Impossible de se connecter au serveur")
