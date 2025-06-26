# GamePad2Car - Contrôle avec Triggers et Son

## Nouveautés

### 🎮 Contrôle par Triggers
- **RT (Right Trigger)** : Accélération/Throttle
- **LT (Left Trigger)** : Freinage/Brake
- **Stick Gauche (X)** : Direction/Steering
- **Bouton Y** : Klaxon 🎵

### 🔊 Système de Son
- Support du klaxon avec le bouton Y
- Fichier son : `assets/circus_horn.mp3`
- Fallback sur plusieurs bibliothèques audio

## Installation

1. Installer les dépendances :
```bash
pip install -r requirements.txt
```

2. Placer un fichier audio pour le klaxon :
```bash
mkdir -p assets
# Copier votre fichier son dans assets/circus_horn.mp3
```

## Tests

### Test des Triggers
```bash
python test_triggers.py
```
Ce script vous aidera à identifier les bons numéros d'axes pour vos triggers.

### Test du Son
```bash
python test_sound.py
```
Vérifiez que le système audio fonctionne correctement.

## Configuration

### Configuration Automatique
```bash
python gamepad2car.py --config
```
Options disponibles :
- Calibrer les triggers (RT/LT)
- Calibrer le steering
- Configurer le servomoteur
- Tester la configuration

### Configuration Manuelle
Éditez `gamepad_config.json` :

```json
{
    "controls": {
        "throttle_axis": 4,  // RT (Right Trigger)
        "brake_axis": 2,     // LT (Left Trigger)  
        "steering_axis": 0,  // Left Stick X
        "horn_btn": 3        // Y Button
    },
    "servo": {
        "enabled": true,
        "center_position": 0.5,
        "min_position": 0.0,
        "max_position": 1.0,
        "invert_direction": false
    }
}
```

## Utilisation

### Démarrage Normal
```bash
python gamepad2car.py
```

### Avec Configuration
```bash
python gamepad2car.py --config
```

## Contrôles

| Contrôle | Action |
|----------|--------|
| RT (Right Trigger) | Accélération |
| LT (Left Trigger) | Freinage |
| Stick Gauche X | Direction |
| Bouton A | Boost temporaire |
| Bouton B | Arrêt d'urgence |
| Bouton X | Marche arrière |
| Bouton Y | Klaxon 🎵 |

## Troubleshooting

### Pas de Son
1. Vérifiez que le fichier `assets/circus_horn.mp3` existe
2. Testez avec `python test_sound.py`
3. Vérifiez que votre système audio fonctionne

### Triggers ne Répondent Pas
1. Testez avec `python test_triggers.py`
2. Notez les numéros d'axes qui changent quand vous appuyez sur les triggers
3. Mettez à jour la configuration avec les bons numéros

### Servo ne Fonctionne Pas
1. Vérifiez que `servo.enabled = true` dans la configuration
2. Calibrez le servomoteur avec `--config`
3. Vérifiez les connexions hardware (pin PB5 sur le VESC)

### Erreurs VESC
1. Vérifiez la connexion série (`/dev/ttyACM0`)
2. Vérifiez les permissions : `sudo chmod 666 /dev/ttyACM0`
3. Vérifiez que le VESC est allumé et connecté

## Architecture

```
gamepad2car.py          # Programme principal
├── gamepad_config.py   # Configuration et calibration
├── gamepad_gui.py      # Interface graphique (optionnelle)
├── test_triggers.py    # Test des triggers
├── test_sound.py       # Test du son
├── assets/
│   └── circus_horn.mp3 # Fichier son du klaxon
└── gamepad_config.json # Configuration sauvegardée
```

## Dépendances

- `pygame>=2.6.0` : Gestion gamepad et audio
- `python-play` : Lecture audio (fallback)
- `playsound>=1.3.0` : Lecture audio (fallback)
- `pyvesc` : Communication avec le contrôleur VESC
- `pyserial>=3.5` : Communication série
- `pythoncrc>=1.2` : Calculs CRC pour VESC
