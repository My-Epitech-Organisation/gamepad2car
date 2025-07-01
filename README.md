# Robocar Control System

Système de contrôle complet pour voiture robotisée utilisant un VESC.

## Vue d'ensemble

Ce projet fournit une plateforme logicielle complète pour contrôler une voiture robotisée de plusieurs façons :
- **Contrôle manuel via manette de jeu** avec basculement vers mode autonome
- **Contrôle simple via clavier** pour les tests
- **Contrôle autonome via IA** recevant des commandes par réseau UDP

## Architecture

### Fichiers principaux

- **`robocar_base.py`** : Classe de base avec toutes les fonctionnalités de sécurité
- **`hybrid_control.py`** : Contrôle hybride manette/IA (recommandé)
- **`keyboard_control.py`** : Contrôle simple au clavier pour tests
- **`scripts/find_gamepad_mappings.py`** : Utilitaire de diagnostic manette

### Fonctionnalités de sécurité (robocar_base.py)

- **Lissage des commandes** : Évite les à-coups dangereux
- **Protection contre les déconnexions** : Gère les coupures d'alimentation (OVP)
- **Surveillance électrique** : Monitoring de la consommation
- **Arrêt d'urgence** : Commandes d'arrêt immédiat
- **Gestion des erreurs robuste** : Redémarrage propre après incident

### Fonctionnalités utilisateur

- **Audio** : Sons d'interface, klaxon, notifications
- **Vitesse variable** : Ajustement en temps réel de la vitesse max
- **Interface intuitive** : Feedback visuel et sonore
- **Mode débogage** : Monitoring des paramètres en temps réel

## Configuration

### Matériel requis
- Voiture robotisée avec contrôleur VESC
- Manette de jeu compatible (ex: Logitech F710)
- Connexion série USB vers VESC

### Configuration logicielle

Modifiez `ROBOCAR_CONFIG` dans `robocar_base.py` :
```python
ROBOCAR_CONFIG = {
    'port': '/dev/ttyACM1',     # Port série du VESC
    'baudrate': 115200,
    'throttle_max': 0.1,        # Puissance max (0.0 à 0.5)
    'steering_left': 0.0,       # Limite gauche servo
    'steering_right': 1.0,      # Limite droite servo
    'steering_center': 0.5      # Position centre servo
}
```

## Utilisation

### 1. Contrôle hybride (recommandé)
```bash
python3 hybrid_control.py
```

**Mode MANUEL** (par défaut) :
- **Gâchette droite (RT)** : Accélération
- **Gâchette gauche (LT)** : Marche arrière/frein
- **Joystick gauche (horizontal)** : Direction
- **Bouton Y** : Klaxon
- **Boutons LB/RB** : Diminuer/Augmenter vitesse max
- **D-Pad** : Sons divers (Epitech, Peter, etc.)
- **Bouton X** : Basculer vers mode AUTONOME
- **Bouton Start** : Quitter

**Mode AUTONOME** :
- Commandes reçues via UDP sur `127.0.0.1:12345`
- Format : `"throttle;steering"` (ex: `"0.5;-0.3"`)
- **Bouton X** : Retour en mode MANUEL

### 2. Contrôle clavier (tests)
```bash
python3 keyboard_control.py
```

- **Flèches** : Direction et mouvement
- **h** : Klaxon  
- **+/-** : Vitesse max
- **s** : Arrêt d'urgence
- **ESC** : Quitter

### 3. Diagnostic manette
```bash
python3 scripts/find_gamepad_mappings.py
```

## Envoi de commandes IA (UDP)

Exemple Python pour contrôle autonome :
```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Avancer doucement en tournant légèrement à droite
sock.sendto("0.3;0.2".encode(), ('127.0.0.1', 12345))
sock.close()
```

## Dépendances

```bash
pip install pygame pynput pyvesc
```

## Sécurité

⚠️ **Important** :
- Commencez toujours avec `throttle_max` faible (0.1)
- Testez dans un environnement sûr
- Gardez un accès à l'arrêt d'urgence
- Surveillez l'alimentation (protection OVP)

## Dépannage

### Problèmes courants
- **"Aucune manette détectée"** : Vérifiez la connexion USB et les permissions
- **"Connexion VESC impossible"** : Vérifiez le port série dans la config
- **"Connexion perdue (OVP)"** : L'alimentation s'est coupée, normal en cas de surcharge

### Logs utiles
Le programme affiche en temps réel :
- État de la connexion VESC
- Commandes envoyées (throttle/steering)
- Vitesse max actuelle
- Alertes de sécurité

## Développement

Pour ajouter de nouvelles fonctionnalités :
1. Modifiez `robocar_base.py` pour les fonctionnalités bas niveau
2. Étendez `hybrid_control.py` pour l'interface utilisateur
3. Testez avec `keyboard_control.py` pour les tests rapides
