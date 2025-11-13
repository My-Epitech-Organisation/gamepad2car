"""
watchdog.py

Système de surveillance de timeout pour la sécurité du Robocar.
Arrête progressivement le véhicule si aucune commande n'est reçue.
"""

import time
import threading
from typing import Optional


class Watchdog:
    """
    Surveillant de timeout pour sécurité.
    
    Ralentit progressivement puis arrête le véhicule si aucune
    commande n'est reçue pendant un certain temps.
    """
    
    def __init__(
        self,
        robocar_instance,
        timeout: float = 0.5,
        stop_timeout: float = 1.0,
        check_interval: float = 0.1
    ):
        """
        Initialise le watchdog.
        
        Args:
            robocar_instance: Instance de Robocar à surveiller
            timeout: Délai avant ralentissement progressif (secondes)
            stop_timeout: Délai avant arrêt complet (secondes)
            check_interval: Fréquence de vérification (secondes)
        """
        self.robocar = robocar_instance
        self.timeout = timeout
        self.stop_timeout = stop_timeout
        self.check_interval = check_interval
        
        self.last_command_time = time.time()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        self.timeout_triggered = False
        self.stop_triggered = False
        
        print(f"⏱️  Watchdog initialisé: timeout={timeout}s, stop={stop_timeout}s")
    
    def update_last_command(self):
        """
        Met à jour le timestamp de la dernière commande reçue.
        Doit être appelé à chaque commande de contrôle valide.
        """
        self.last_command_time = time.time()
        self.timeout_triggered = False
        self.stop_triggered = False
    
    def start(self):
        """Démarre le thread de surveillance."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self.thread.start()
        print("⏱️  Watchdog démarré")
    
    def stop(self):
        """Arrête le thread de surveillance."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        print("⏱️  Watchdog arrêté")
    
    def _watchdog_loop(self):
        """Boucle principale du watchdog (thread séparé)."""
        while self.running:
            elapsed = time.time() - self.last_command_time
            
            # Arrêt complet si timeout dépassé
            if elapsed > self.stop_timeout:
                if not self.stop_triggered:
                    print(f"\n⚠️  WATCHDOG: Timeout {elapsed:.2f}s > {self.stop_timeout}s - ARRÊT D'URGENCE")
                    try:
                        self.robocar.emergency_stop()
                    except Exception as e:
                        print(f"❌ Erreur lors de l'arrêt d'urgence: {e}")
                    self.stop_triggered = True
            
            # Ralentissement progressif entre timeout et stop_timeout
            elif elapsed > self.timeout:
                if not self.timeout_triggered:
                    print(f"\n⚠️  WATCHDOG: Timeout {elapsed:.2f}s - Ralentissement progressif...")
                    self.timeout_triggered = True
                
                # Calculer le facteur de réduction (décroissance linéaire)
                # À timeout: 100%, à stop_timeout: 0%
                remaining_time = self.stop_timeout - elapsed
                time_window = self.stop_timeout - self.timeout
                reduction_factor = max(0.0, remaining_time / time_window)
                
                # Appliquer la réduction progressive
                try:
                    current_throttle = self.robocar.current_throttle
                    target_throttle = current_throttle * reduction_factor
                    self.robocar.set_throttle(target_throttle)
                except Exception as e:
                    print(f"❌ Erreur lors du ralentissement: {e}")
            
            time.sleep(self.check_interval)
    
    def get_elapsed_time(self) -> float:
        """Retourne le temps écoulé depuis la dernière commande."""
        return time.time() - self.last_command_time
    
    def get_status(self) -> dict:
        """
        Retourne l'état actuel du watchdog.
        
        Returns:
            Dict avec elapsed_time, timeout_triggered, stop_triggered
        """
        elapsed = self.get_elapsed_time()
        return {
            'elapsed_time': elapsed,
            'timeout_triggered': self.timeout_triggered,
            'stop_triggered': self.stop_triggered,
            'is_active': elapsed > self.timeout
        }


# --- TEST ---
if __name__ == "__main__":
    print("=== Test Watchdog ===\n")
    
    # Mock d'un Robocar pour test
    class MockRobocar:
        def __init__(self):
            self.current_throttle = 0.5
        
        def set_throttle(self, value):
            self.current_throttle = value
            print(f"  → Throttle réglé à {value:.2f}")
        
        def emergency_stop(self):
            self.current_throttle = 0.0
            print("  → ARRÊT D'URGENCE")
    
    mock_car = MockRobocar()
    watchdog = Watchdog(mock_car, timeout=2.0, stop_timeout=4.0, check_interval=0.5)
    
    watchdog.start()
    
    print("Simulation: envoi de commandes pendant 1.5s, puis arrêt...")
    
    # Envoyer des commandes pendant 1.5s
    for i in range(3):
        print(f"\n[{i+1}] Envoi commande...")
        watchdog.update_last_command()
        time.sleep(0.5)
    
    # Arrêter d'envoyer et observer le watchdog
    print("\n⏸️  Arrêt des commandes - Watchdog doit se déclencher...\n")
    
    try:
        time.sleep(5)  # Attendre que le watchdog se déclenche
    except KeyboardInterrupt:
        print("\nInterrompu")
    
    watchdog.stop()
    print("\n=== Test terminé ===")
