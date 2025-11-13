"""
keyboard_client.py

Client de contrôle au clavier pour Robocar.
Alternative à la manette pour tests et contrôle d'urgence.
"""

import time
from typing import Optional, Dict, Any, Set
from pynput import keyboard

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clients.base_client import BaseClient
from core.protocol import CommandType


class KeyboardClient(BaseClient):
    """
    Client de contrôle au clavier.
    
    Mapping:
    - Z/S : Accélération avant/arrière
    - Q/D : Direction gauche/droite
    - Espace : Frein d'urgence
    - K : Klaxon
    - +/- : Augmenter/diminuer vitesse max
    - Flèches : Sons (UP/DOWN/LEFT/RIGHT)
    - Échap : Quitter
    """
    
    def __init__(
        self,
        server_ip: str = "127.0.0.1",
        config_file: Optional[str] = "config/client_config.yaml"
    ):
        """
        Initialise le client clavier.
        
        Args:
            server_ip: Adresse IP du serveur
            config_file: Fichier de configuration
        """
        super().__init__(
            client_id="keyboard_client",
            server_ip=server_ip,
            config_file=config_file
        )
        
        # État clavier
        self.keys_pressed: Set[keyboard.Key] = set()
        self.keys_char_pressed: Set[str] = set()
        
        # État contrôle
        self.throttle = 0.0
        self.steering = 0.0
        
        # Configuration
        self.throttle_increment = 0.05
        self.steering_value = 0.5
        self.smooth_release_time = 0.5
        
        # Listener clavier
        self.keyboard_listener: Optional[keyboard.Listener] = None
        self.running = False
    
    def _on_press(self, key):
        """Callback Appui touche."""
        try:
            if hasattr(key, 'char') and key.char:
                self.keys_char_pressed.add(key.char.lower())
            else:
                self.keys_pressed.add(key)
        except AttributeError:
            pass
    
    def _on_release(self, key):
        """Callback Relâchement touche."""
        try:
            if hasattr(key, 'char') and key.char:
                self.keys_char_pressed.discard(key.char.lower())
            else:
                self.keys_pressed.discard(key)
            
            # Échap pour quitter
            if key == keyboard.Key.esc:
                self.running = False
                return False  # Arrête le listener
        
        except AttributeError:
            pass
    
    def _update_control_values(self):
        """Met à jour throttle et steering selon touches pressées."""
        # --- THROTTLE ---
        if 'z' in self.keys_char_pressed:
            # Accélérer
            self.throttle += self.throttle_increment
            self.throttle = min(1.0, self.throttle)
        elif 's' in self.keys_char_pressed:
            # Freiner/reculer
            self.throttle -= self.throttle_increment
            self.throttle = max(-1.0, self.throttle)
        else:
            # Retour progressif à 0
            if abs(self.throttle) > 0.01:
                decay = self.throttle_increment * 2
                if self.throttle > 0:
                    self.throttle = max(0, self.throttle - decay)
                else:
                    self.throttle = min(0, self.throttle + decay)
        
        # Frein d'urgence (espace)
        if keyboard.Key.space in self.keys_pressed:
            self.throttle = 0.0
        
        # --- STEERING ---
        if 'q' in self.keys_char_pressed:
            # Tourner gauche
            self.steering = -self.steering_value
        elif 'd' in self.keys_char_pressed:
            # Tourner droite
            self.steering = self.steering_value
        else:
            # Retour au centre
            self.steering = 0.0
    
    def _check_commands(self) -> list:
        """Vérifie les commandes ponctuelles."""
        commands = []
        
        # Klaxon (K maintenu)
        if 'k' in self.keys_char_pressed:
            commands.append(CommandType.HORN)
        
        # Vitesse +/-
        if '+' in self.keys_char_pressed or '=' in self.keys_char_pressed:
            commands.append(CommandType.INCREASE_SPEED)
            time.sleep(0.2)  # Éviter répétition trop rapide
        
        if '-' in self.keys_char_pressed or '_' in self.keys_char_pressed:
            commands.append(CommandType.DECREASE_SPEED)
            time.sleep(0.2)
        
        # Sons via flèches
        if keyboard.Key.up in self.keys_pressed:
            commands.append(CommandType.SOUND_EPITECH)
            time.sleep(0.3)
        if keyboard.Key.down in self.keys_pressed:
            commands.append(CommandType.SOUND_SATELISATION)
            time.sleep(0.3)
        if keyboard.Key.right in self.keys_pressed:
            commands.append(CommandType.SOUND_PETER)
            time.sleep(0.3)
        if keyboard.Key.left in self.keys_pressed:
            commands.append(CommandType.SOUND_POLIZIA)
            time.sleep(0.3)
        
        return commands
    
    def get_control_input(self) -> Dict[str, float]:
        """Retourne les valeurs de contrôle actuelles."""
        return {
            'throttle': self.throttle,
            'steering': self.steering
        }
    
    def run(self):
        """
        Boucle principale du client clavier.
        """
        print("=== Robocar Keyboard Client ===\n")
        print("📋 Contrôles:")
        print("  Z : Accélérer")
        print("  S : Freiner/Reculer")
        print("  Q : Tourner gauche")
        print("  D : Tourner droite")
        print("  Espace : Frein d'urgence")
        print("  K : Klaxon")
        print("  +/- : Augmenter/diminuer vitesse max")
        print("  Flèches : Sons (UP/DOWN/LEFT/RIGHT)")
        print("  Échap : Quitter")
        print("\n" + "="*40 + "\n")
        
        # Connecter au serveur
        if not self.connect():
            print("❌ Impossible de se connecter au serveur")
            return
        
        print(f"✅ Connecté au serveur {self.server_ip}:{self.control_port}")
        print("⌨️  Contrôle actif - Utilisez le clavier\n")
        
        # Démarrer listener clavier
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.keyboard_listener.start()
        
        self.running = True
        
        try:
            while self.running and self.connected:
                # Mettre à jour valeurs de contrôle
                self._update_control_values()
                
                # Vérifier commandes
                commands = self._check_commands()
                
                # Envoyer au serveur
                self.send_control(
                    throttle=self.throttle,
                    steering=self.steering,
                    commands=commands if commands else None
                )
                
                # Afficher état
                telem = self.get_last_telemetry()
                throttle_max = telem.get('throttle_max', 0.0) if telem else 0.0
                latency = self.get_telemetry_age()
                
                # Indicateur de connexion
                if latency < 0.5:
                    conn_indicator = "🟢"
                elif latency < 2.0:
                    conn_indicator = "🟡"
                else:
                    conn_indicator = "🔴"
                
                print(f"{conn_indicator} Accél: {self.throttle:>6.2f} | Dir: {self.steering:>5.2f} | "
                      f"Max: {throttle_max:.1f} | Latence: {latency*1000:.0f}ms", end="\r")
                
                time.sleep(0.05)  # 20Hz
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrompu par l'utilisateur")
        
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n")
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            self.disconnect()
            print("⌨️  Client clavier terminé proprement.")


# --- MAIN ---
def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Robocar Keyboard Client")
    parser.add_argument(
        '--server-ip',
        default='127.0.0.1',
        help='Adresse IP du serveur Robocar'
    )
    parser.add_argument(
        '--config',
        default='config/client_config.yaml',
        help='Fichier de configuration'
    )
    args = parser.parse_args()
    
    client = KeyboardClient(
        server_ip=args.server_ip,
        config_file=args.config
    )
    
    client.run()


if __name__ == "__main__":
    main()
