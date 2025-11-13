"""
telemetry_publisher.py

Module de publication de télémétrie pour le serveur Robocar.
Envoie l'état du robot en broadcast UDP à intervalle régulier.
"""

import socket
import time
import threading
from typing import Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.protocol import create_telemetry_message


class TelemetryPublisher:
    """
    Publie la télémétrie du Robocar en broadcast UDP.
    
    Tous les clients connectés reçoivent automatiquement
    l'état en temps réel sans avoir à s'enregistrer.
    """
    
    def __init__(
        self,
        robocar_instance,
        port: int = 5001,
        publish_rate_hz: float = 20.0,
        active_client_id: Optional[str] = None
    ):
        """
        Initialise le publisher de télémétrie.
        
        Args:
            robocar_instance: Instance de Robocar à surveiller
            port: Port UDP pour broadcast
            publish_rate_hz: Fréquence d'envoi (Hz)
            active_client_id: ID du client actif (optionnel)
        """
        self.robocar = robocar_instance
        self.port = port
        self.publish_rate = publish_rate_hz
        self.publish_interval = 1.0 / publish_rate_hz
        self.active_client_id = active_client_id
        
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        self.start_time = time.time()
        self.message_count = 0
        
        print(f"📡 TelemetryPublisher initialisé: port={port}, rate={publish_rate_hz}Hz")
    
    def start(self):
        """Démarre la publication de télémétrie."""
        if self.running:
            return
        
        try:
            # Créer socket UDP avec broadcast activé
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            self.running = True
            self.thread = threading.Thread(target=self._publish_loop, daemon=True)
            self.thread.start()
            
            print("📡 Publication télémétrie démarrée")
            
        except Exception as e:
            print(f"❌ Erreur démarrage telemetry: {e}")
            self.running = False
    
    def stop(self):
        """Arrête la publication."""
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        
        if self.socket:
            self.socket.close()
        
        print("📡 Publication télémétrie arrêtée")
    
    def set_active_client(self, client_id: Optional[str]):
        """Définit l'ID du client actif."""
        self.active_client_id = client_id
    
    def _collect_telemetry(self) -> dict:
        """
        Collecte les données de télémétrie du Robocar.
        
        Returns:
            Dict avec toutes les données d'état
        """
        try:
            # Données de base toujours disponibles
            data = {
                'current_throttle': self.robocar.current_throttle,
                'current_steering': 0.0,  # TODO: ajouter steering actuel dans Robocar
                'throttle_max': self.robocar.throttle_max_power,
                'battery_voltage': None,
                'battery_current': None,
                'connection_status': "ok",
                'active_client': self.active_client_id,
                'uptime': time.time() - self.start_time
            }
            
            # Essayer de récupérer les mesures VESC
            if self.robocar.is_connected:
                try:
                    measurements = self.robocar.vesc.get_measurements()
                    data['battery_voltage'] = measurements.input_voltage
                    data['battery_current'] = measurements.input_current
                except:
                    pass  # Mesures VESC pas disponibles, on continue
                
                # Vérifier l'état de connexion
                if hasattr(self.robocar, 'connection_lost') and self.robocar.connection_lost:
                    data['connection_status'] = "lost"
                elif hasattr(self.robocar, 'emergency_triggered') and self.robocar.emergency_triggered:
                    data['connection_status'] = "emergency"
            else:
                data['connection_status'] = "disconnected"
            
            return data
            
        except Exception as e:
            print(f"⚠️  Erreur collecte télémétrie: {e}")
            return {
                'current_throttle': 0.0,
                'current_steering': 0.0,
                'throttle_max': 0.0,
                'battery_voltage': None,
                'battery_current': None,
                'connection_status': "error",
                'active_client': None,
                'uptime': 0.0
            }
    
    def _publish_loop(self):
        """Boucle principale de publication (thread séparé)."""
        next_publish = time.time()
        
        while self.running:
            current_time = time.time()
            
            # Attendre le prochain intervalle
            if current_time < next_publish:
                time.sleep(0.001)  # Sleep court pour ne pas bloquer
                continue
            
            # Collecter et envoyer télémétrie
            try:
                telemetry_data = self._collect_telemetry()
                
                message = create_telemetry_message(
                    current_throttle=telemetry_data['current_throttle'],
                    current_steering=telemetry_data['current_steering'],
                    throttle_max=telemetry_data['throttle_max'],
                    battery_voltage=telemetry_data['battery_voltage'],
                    battery_current=telemetry_data['battery_current'],
                    connection_status=telemetry_data['connection_status'],
                    active_client=telemetry_data['active_client'],
                    uptime=telemetry_data['uptime']
                )
                
                # Envoyer en broadcast
                self.socket.sendto(
                    message.encode('utf-8'),
                    ('<broadcast>', self.port)
                )
                
                self.message_count += 1
                
            except Exception as e:
                if self.running:  # Ne log que si on devrait être actif
                    print(f"❌ Erreur envoi télémétrie: {e}")
            
            # Planifier le prochain envoi
            next_publish += self.publish_interval
    
    def get_stats(self) -> dict:
        """
        Retourne des statistiques sur la publication.
        
        Returns:
            Dict avec uptime, message_count, publish_rate
        """
        uptime = time.time() - self.start_time
        actual_rate = self.message_count / uptime if uptime > 0 else 0
        
        return {
            'uptime': uptime,
            'message_count': self.message_count,
            'target_rate_hz': self.publish_rate,
            'actual_rate_hz': actual_rate
        }


# --- TEST ---
if __name__ == "__main__":
    print("=== Test TelemetryPublisher ===\n")
    
    # Mock d'un Robocar pour test
    class MockRobocar:
        def __init__(self):
            self.current_throttle = 0.3
            self.throttle_max_power = 0.2
            self.is_connected = True
            self.connection_lost = False
            self.emergency_triggered = False
    
    mock_car = MockRobocar()
    publisher = TelemetryPublisher(
        mock_car,
        port=5001,
        publish_rate_hz=5.0,  # 5Hz pour test
        active_client_id="test_client"
    )
    
    publisher.start()
    
    print("Publication pendant 5 secondes...")
    print("(Utilisez `nc -lu 5001` dans un autre terminal pour voir les messages)\n")
    
    try:
        for i in range(5):
            time.sleep(1)
            # Modifier l'état pour voir les changements
            mock_car.current_throttle = 0.1 * (i + 1)
            
            stats = publisher.get_stats()
            print(f"[{i+1}s] Messages envoyés: {stats['message_count']}, "
                  f"Rate: {stats['actual_rate_hz']:.1f} Hz")
    
    except KeyboardInterrupt:
        print("\nInterrompu")
    
    publisher.stop()
    
    final_stats = publisher.get_stats()
    print(f"\n=== Statistiques finales ===")
    print(f"Uptime: {final_stats['uptime']:.1f}s")
    print(f"Messages: {final_stats['message_count']}")
    print(f"Rate moyenne: {final_stats['actual_rate_hz']:.1f} Hz")
    print("\n=== Test terminé ===")
