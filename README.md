# Gamepad2Car - Architecture Client-Serveur

Système de contrôle modulaire pour Robocar avec architecture réseau découplée.

## 🏗️ Architecture

Le système est composé de :
- **Serveur** : Tourne sur le robot (Raspberry Pi), contrôle le VESC
- **Clients** : Sources de contrôle multiples (gamepad, clavier, IA...)
- **Protocole** : Communication UDP + JSON pour faible latence

```
┌─────────────────────────────┐
│        CLIENTS              │
│  • gamepad_client.py        │
│  • keyboard_client.py       │
│  • autonomous_client.py     │
└──────────┬──────────────────┘
           │ UDP JSON
           │ Port 5000
           ↓
┌─────────────────────────────┐
│     SERVER (Raspberry)      │
│  robocar_server.py          │
│  ├─ Commandes réseau        │
│  ├─ Watchdog sécurité       │
│  ├─ Télémétrie (5001)       │
│  └─ Interface VESC          │
└──────────┬──────────────────┘
           │
           ↓
      ┌────────┐
      │  VESC  │
      │ Motors │
      └────────┘
```

## 🚀 Démarrage Rapide

### 1. Build Docker Image

```bash
cd /home/psalmon/Documents/Robocar/gamepad2car/gamepad2car
./scripts/build.sh
```

### 2. Lancer le Serveur (sur le robot)

```bash
./scripts/run_server.sh
```

Le serveur écoute sur :
- Port 5000 (UDP) : Réception commandes
- Port 5001 (UDP) : Broadcast télémétrie

### 3. Lancer un Client

**Option A - Gamepad (manette de jeu)** :
```bash
./scripts/run_gamepad_client.sh [SERVER_IP]
```

**Option B - Clavier** :
```bash
./scripts/run_keyboard_client.sh [SERVER_IP]
```

**Exemple avec serveur distant** :
```bash
./scripts/run_gamepad_client.sh 192.168.1.100
```

## 🎮 Contrôles Gamepad

| Commande | Input | Détails |
|----------|-------|---------|
| Accélération | Gâchette DROITE (RT) | Axe 5 |
| Marche arrière | Gâchette GAUCHE (LT) | Axe 2 |
| Direction | Joystick GAUCHE (↔) | Axe 0 |
| Klaxon | Bouton Y | Bouton 3 |
| Vitesse + | RB | Bouton 5 |
| Vitesse - | LB | Bouton 4 |
| **Sons via D-Pad** | | |
| Epitech | D-Pad UP | |
| Satelisation | D-Pad DOWN | |
| Peter | D-Pad RIGHT | |
| Polizia | D-Pad LEFT | |
| Quitter | START | Bouton 8 |

## ⌨️ Contrôles Clavier

| Touche | Action |
|--------|--------|
| Z | Accélérer |
| S | Freiner/Reculer |
| Q | Tourner gauche |
| D | Tourner droite |
| Espace | Frein d'urgence |
| K | Klaxon |
| +/- | Augmenter/diminuer vitesse max |
| Flèches | Sons (UP/DOWN/LEFT/RIGHT) |
| Échap | Quitter |

## 📡 Protocole de Communication

### Message de Contrôle (Client → Serveur)

```json
{
  "version": "1.0",
  "timestamp": 1699876543.123,
  "source": "gamepad_client",
  "type": "control",
  "data": {
    "throttle": 0.5,
    "steering": -0.3,
    "throttle_max": 0.3
  },
  "commands": ["horn"],
  "sequence": 42
}
```

### Message de Télémétrie (Serveur → Clients)

```json
{
  "version": "1.0",
  "timestamp": 1699876543.456,
  "type": "telemetry",
  "data": {
    "current_throttle": 0.48,
    "current_steering": -0.28,
    "throttle_max": 0.3,
    "battery_voltage": 11.8,
    "battery_current": 2.3,
    "connection_status": "ok",
    "active_client": "gamepad_client",
    "uptime": 123.4
  }
}
```

## 🔧 Configuration

### Serveur (`config/server_config.yaml`)

```yaml
server:
  control_port: 5000
  telemetry_port: 5001
  telemetry_rate_hz: 20

safety:
  watchdog_timeout_ms: 500
  emergency_stop_timeout_ms: 1000

robocar:
  port: /dev/ttyACM0
  baudrate: 115200
  throttle_max: 0.1
```

### Client (`config/client_config.yaml`)

```yaml
client:
  server_ip: 127.0.0.1
  control_port: 5000
  telemetry_port: 5001
  
gamepad:
  joystick_deadzone: 0.1
  
keyboard:
  throttle_increment: 0.05
```

## 🛡️ Sécurité

### Watchdog Automatique

Le serveur surveille les commandes reçues :
- **< 500ms** : Fonctionnement normal
- **> 500ms** : Ralentissement progressif
- **> 1000ms** : Arrêt d'urgence

### Lissage du Throttle

Protection contre les changements brusques :
- Filtre alpha : 0.2
- Changement max par cycle : 0.03
- Évite les pics de courant dangereux

## 🗂️ Structure du Projet

```
gamepad2car/
├── core/                      # Modules de base
│   ├── protocol.py           # Définition protocole JSON
│   └── robocar_base.py       # Interface VESC
│
├── server/                    # Serveur Robocar
│   ├── robocar_server.py     # Serveur principal
│   ├── telemetry_publisher.py# Publication état
│   └── watchdog.py           # Sécurité timeout
│
├── clients/                   # Clients de contrôle
│   ├── base_client.py        # Classe abstraite
│   ├── gamepad_client.py     # Client manette
│   └── keyboard_client.py    # Client clavier
│
├── tools/                     # Outils
│   └── find_gamepad_mappings.py  # Détection boutons
│
├── config/                    # Configuration
│   ├── server_config.yaml
│   └── client_config.yaml
│
├── logs/                      # Logs (auto-généré)
│   ├── server_YYYYMMDD.log
│   └── session_YYYYMMDD_HHMMSS.jsonl
│
├── scripts/                   # Scripts de lancement
│   ├── build.sh
│   ├── run_server.sh
│   ├── run_gamepad_client.sh
│   └── run_keyboard_client.sh
│
└── Dockerfile.base            # Image Docker
```

## 🛠️ Troubleshooting

### Le client ne se connecte pas au serveur

```bash
# Vérifier que le serveur tourne
ping 192.168.1.100

# Vérifier les ports (sur le serveur)
sudo netstat -ulnp | grep 5000

# Tester avec netcat
nc -u 192.168.1.100 5000
```

### Latence élevée

- Utiliser WiFi 5GHz au lieu de 2.4GHz
- Rapprocher client du serveur
- Vérifier charge réseau :
  ```bash
  ping -c 100 192.168.1.100
  ```

### Le VESC ne répond pas

```bash
# Vérifier présence du device
ls -l /dev/ttyACM0

# Vérifier permissions
sudo chmod 666 /dev/ttyACM0

# Tester connexion série
sudo screen /dev/ttyACM0 115200
```

### Firewall bloque les ports

```bash
# Autoriser ports UDP
sudo ufw allow 5000:5001/udp

# Ou désactiver temporairement
sudo ufw disable
```

## 📊 Monitoring

### Logs Serveur

```bash
# Logs en temps réel
tail -f logs/server_$(date +%Y%m%d).log

# Rechercher erreurs
grep ERROR logs/server_*.log
```

### Sessions de Contrôle

Les sessions sont enregistrées en JSON lines :
```bash
# Voir dernière session
tail logs/session_*.jsonl

# Compter commandes
wc -l logs/session_*.jsonl
```

## 🔬 Développement

### Tester le Protocole

```bash
# Test protocol.py
python3 core/protocol.py

# Test base_client.py
python3 clients/base_client.py

# Test watchdog.py
python3 server/watchdog.py
```

### Créer un Nouveau Client

1. Hériter de `BaseClient`
2. Implémenter `get_control_input()`
3. Implémenter `run()`

Exemple minimal :
```python
from clients.base_client import BaseClient

class MyClient(BaseClient):
    def get_control_input(self):
        return {'throttle': 0.3, 'steering': 0.0}
    
    def run(self):
        if self.connect():
            while self.running:
                control = self.get_control_input()
                self.send_control(**control)
                time.sleep(0.02)
```

## 📈 Performance

### Latence Typique

| Environnement | Latence |
|---------------|---------|
| Localhost (127.0.0.1) | 5-10ms |
| Ethernet local | 10-20ms |
| WiFi 5GHz | 20-50ms |
| WiFi 2.4GHz | 50-100ms |

### Débit

- **Commandes** : ~50 msg/s (20ms interval)
- **Télémétrie** : 20 msg/s (50ms interval)
- **Bandwidth** : ~10 KB/s par client

## 🎯 Roadmap

### Implémenté ✅
- [x] Architecture client-serveur
- [x] Client gamepad
- [x] Client clavier
- [x] Télémétrie temps réel
- [x] Watchdog sécurité
- [x] Configuration YAML
- [x] Logging sessions

### À venir 🚧
- [ ] Client autonome (IA)
- [ ] Interface web (dashboard)
- [ ] Replay de trajectoires
- [ ] Support multi-véhicules
- [ ] Authentification clients
- [ ] Chiffrement communication

## 📝 Licence

MIT License - Voir fichier LICENSE

## 👥 Contributeurs

- **Auteur original** : gamepad_control.py
- **Architecture réseau** : GitHub Copilot + Paul Salmon

## 🆘 Support

Pour toute question ou problème :
1. Vérifier logs dans `logs/`
2. Consulter ce README
3. Ouvrir une issue sur GitHub

---

**Version** : 2.0.0 (Architecture Client-Serveur)
**Date** : Novembre 2025
