"""
gamepad_client.py

Client de contrôle via manette de jeu pour Robocar.
Adapté du code original gamepad_control.py pour architecture réseau.
"""

import pygame
import time
from typing import Optional, Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clients.base_client import BaseClient
from core.protocol import CommandType


# --- CONFIGURATION DE LA MANETTE (Style "Jeu de Course") ---
# Axes (VÉRIFIEZ AVEC tools/find_gamepad_mappings.py !)
STEERING_AXIS = 0  # Joystick GAUCHE, axe horizontal
REVERSE_AXIS = 2   # Gâchette GAUCHE (LT)
FORWARD_AXIS = 5   # Gâchette DROITE (RT)

# Boutons
EXIT_BUTTON = 8      # Bouton "Start" ou "Logitech"
KLAXON_BUTTON = 3    # Bouton Y (Klaxon)
SPEED_DOWN = 4       # LB
SPEED_UP = 5         # RB

# Zone morte pour la direction afin d'aller bien droit
JOYSTICK_DEADZONE = 0.1
# --------------------------------------------------------


class GamepadClient(BaseClient):
    """
    Client de contrôle par manette de jeu.
    
    Hérite de BaseClient et implémente la logique spécifique
    à la lecture d'une manette Pygame.
    """
    
    def __init__(
        self,
        server_ip: str = "127.0.0.1",
        config_file: Optional[str] = "config/client_config.yaml"
    ):
        """
        Initialise le client gamepad.
        
        Args:
            server_ip: Adresse IP du serveur Robocar
            config_file: Fichier de configuration (optionnel)
        """
        super().__init__(
            client_id="gamepad_client",
            server_ip=server_ip,
            config_file=config_file
        )
        
        # État gamepad
        self.joystick: Optional[pygame.joystick.Joystick] = None
        self.throttle_value = 0.0
        self.steering_value = 0.0
        self.previous_hat = (0, 0)
        
        # Configuration depuis YAML
        self._load_gamepad_config()
        
        # Stats affichage
        self.last_telemetry_display = 0
        self.display_interval = 0.5  # Afficher toutes les 0.5s
    
    def _load_gamepad_config(self):
        """Charge la config spécifique gamepad depuis YAML."""
        # TODO: Charger depuis config si disponible
        pass
    
    def _init_gamepad(self) -> bool:
        """
        Initialise Pygame et la manette.
        
        Returns:
            True si manette détectée et initialisée
        """
        pygame.init()
        pygame.joystick.init()
        
        if pygame.joystick.get_count() == 0:
            print("❌ ERREUR: Aucune manette détectée.")
            return False
        
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        
        print(f"🎮 Manette détectée : {self.joystick.get_name()}")
        print("\n--- CONTRÔLES ACTIFS (Style Course v2) ---")
        print(f"Accélération : Gâchette DROITE (RT)")
        print(f"Marche arrière/Frein : Gâchette GAUCHE (LT)")
        print(f"Direction : Joystick GAUCHE (gauche/droite)")
        print(f"Klaxon : Bouton Y (bouton {KLAXON_BUTTON})")
        print(f"Sons : D-Pad (UP/DOWN/LEFT/RIGHT)")
        print(f"Vitesse +/- : Boutons LB/RB")
        print(f"QUITTER : Bouton 'Start' (bouton {EXIT_BUTTON})")
        print("-------------------------------------------\n")
        
        return True
    
    def _setup_telemetry_callback(self):
        """Configure le callback de télémétrie."""
        def on_telemetry(data: Dict[str, Any]):
            # Afficher seulement périodiquement
            current_time = time.time()
            if current_time - self.last_telemetry_display > self.display_interval:
                battery = data.get('battery_voltage')
                current = data.get('battery_current')
                status = data.get('connection_status', 'unknown')
                
                battery_str = f"{battery:.1f}V" if battery else "N/A"
                current_str = f"{current:.1f}A" if current else "N/A"
                
                print(f"📊 Batterie: {battery_str} | {current_str} | Status: {status}")
                self.last_telemetry_display = current_time
        
        self.set_telemetry_callback(on_telemetry)
    
    def get_control_input(self) -> Dict[str, float]:
        """
        Lit les entrées de la manette.
        
        Returns:
            Dict avec throttle et steering
        """
        if not self.joystick:
            return {'throttle': 0.0, 'steering': 0.0}
        
        return {
            'throttle': self.throttle_value,
            'steering': self.steering_value
        }
    
    def run(self):
        """
        Boucle principale du client gamepad.
        
        Lit la manette et envoie les commandes au serveur.
        """
        # Initialiser gamepad
        if not self._init_gamepad():
            return
        
        # Connecter au serveur
        if not self.connect():
            print("❌ Impossible de se connecter au serveur")
            pygame.quit()
            return
        
        # Setup telemetry
        self._setup_telemetry_callback()
        
        # Son d'intro (envoyé au serveur)
        self.send_control(0.0, 0.0, commands=[CommandType.SOUND_EPITECH])
        
        print(f"\n✅ Connecté au serveur {self.server_ip}:{self.control_port}")
        print("🎮 Contrôle actif - Utilisez la manette\n")
        
        # Créer une petite fenêtre Pygame (nécessaire pour les événements)
        screen = pygame.display.set_mode((400, 200))
        pygame.display.set_caption("Robocar - Gamepad Client")
        
        running = True
        
        try:
            while running and self.connected:
                # CRITIQUE: Forcer pygame à actualiser l'état des joysticks
                # Sans cela, get_axis() retourne toujours 0 dans Docker
                pygame.event.pump()
                
                # Traiter événements Pygame
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    
                    elif event.type == pygame.JOYBUTTONDOWN:
                        if event.button == EXIT_BUTTON:
                            print("\n🛑 Bouton de sortie détecté. Arrêt...")
                            running = False
                    
                    elif event.type == pygame.JOYBUTTONUP:
                        if event.button == SPEED_DOWN:
                            self.send_control(0.0, 0.0, commands=[CommandType.DECREASE_SPEED])
                        elif event.button == SPEED_UP:
                            self.send_control(0.0, 0.0, commands=[CommandType.INCREASE_SPEED])
                
                # Lire klaxon (état maintenu)
                commands = []
                if self.joystick.get_button(KLAXON_BUTTON):
                    commands.append(CommandType.HORN)
                
                # Lire D-Pad pour sons
                if self.joystick.get_numhats() > 0:
                    hat_x, hat_y = self.joystick.get_hat(0)
                    if (hat_x, hat_y) != self.previous_hat and (hat_x != 0 or hat_y != 0):
                        if hat_y == 1:
                            commands.append(CommandType.SOUND_EPITECH)
                        elif hat_y == -1:
                            commands.append(CommandType.SOUND_SATELISATION)
                        elif hat_x == 1:
                            commands.append(CommandType.SOUND_PETER)
                        elif hat_x == -1:
                            commands.append(CommandType.SOUND_POLIZIA)
                        self.previous_hat = (hat_x, hat_y)
                    elif hat_x == 0 and hat_y == 0:
                        self.previous_hat = (0, 0)
                
                # 1. Lire la direction depuis le joystick GAUCHE
                steering_value = self.joystick.get_axis(STEERING_AXIS)
                if abs(steering_value) < JOYSTICK_DEADZONE:
                    steering_value = 0.0
                self.steering_value = steering_value
                
                # 2. Lire les gâchettes et les convertir en [0.0, 1.0]
                forward_power = (self.joystick.get_axis(FORWARD_AXIS) + 1) / 2
                reverse_power = (self.joystick.get_axis(REVERSE_AXIS) + 1) / 2
                
                # 3. Calculer l'accélération finale
                throttle_value = forward_power - reverse_power
                self.throttle_value = throttle_value
                
                # 4. Envoyer au serveur
                self.send_control(
                    throttle=throttle_value,
                    steering=steering_value,
                    commands=commands if commands else None
                )
                
                # 5. Afficher en temps réel
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
                
                print(f"{conn_indicator} Accél: {throttle_value:>6.2f} | Dir: {steering_value:>5.2f} | "
                      f"Max: {throttle_max:.1f} | Latence: {latency*1000:.0f}ms", end="\r")
                
                time.sleep(0.02)  # 50Hz
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrompu par l'utilisateur")
        
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n")
            self.disconnect()
            pygame.quit()
            print("🎮 Client gamepad terminé proprement.")


# --- MAIN ---
def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Robocar Gamepad Client")
    parser.add_argument(
        '--server-ip',
        default='127.0.0.1',
        help='Adresse IP du serveur Robocar (défaut: 127.0.0.1)'
    )
    parser.add_argument(
        '--config',
        default='config/client_config.yaml',
        help='Fichier de configuration (défaut: config/client_config.yaml)'
    )
    args = parser.parse_args()
    
    print("=== Robocar Gamepad Client ===\n")
    
    client = GamepadClient(
        server_ip=args.server_ip,
        config_file=args.config
    )
    
    client.run()


if __name__ == "__main__":
    main()
