"""
protocol.py

Définition du protocole de communication réseau pour Robocar.
Format de messages standardisé en JSON pour communication client-serveur.
"""

import json
import time
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple


# --- CONSTANTES ---
PROTOCOL_VERSION = "1.0"


class MessageType(str, Enum):
    """Types de messages supportés par le protocole."""
    CONTROL = "control"           # Commandes de mouvement
    COMMAND = "command"           # Commandes ponctuelles (horn, etc)
    TELEMETRY = "telemetry"       # État du robot
    HEARTBEAT = "heartbeat"       # Keep-alive
    ACK = "ack"                   # Accusé de réception
    ERROR = "error"               # Message d'erreur


class CommandType(str, Enum):
    """Types de commandes ponctuelles."""
    HORN = "horn"
    SOUND_EPITECH = "sound_epitech"
    SOUND_SATELISATION = "sound_satelisation"
    SOUND_PETER = "sound_peter"
    SOUND_POLIZIA = "sound_polizia"
    INCREASE_SPEED = "increase_speed"
    DECREASE_SPEED = "decrease_speed"
    EMERGENCY_STOP = "emergency_stop"


# --- VALIDATION ---

def validate_control_data(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Valide les données d'un message de contrôle.
    
    Args:
        data: Dictionnaire contenant throttle et steering
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Data must be a dictionary"
    
    # Vérifier présence des champs requis
    if 'throttle' not in data:
        return False, "Missing 'throttle' field"
    if 'steering' not in data:
        return False, "Missing 'steering' field"
    
    # Valider throttle
    try:
        throttle = float(data['throttle'])
        if not -1.0 <= throttle <= 1.0:
            return False, f"Throttle {throttle} out of range [-1.0, 1.0]"
    except (ValueError, TypeError):
        return False, "Throttle must be a number"
    
    # Valider steering
    try:
        steering = float(data['steering'])
        if not -1.0 <= steering <= 1.0:
            return False, f"Steering {steering} out of range [-1.0, 1.0]"
    except (ValueError, TypeError):
        return False, "Steering must be a number"
    
    # Valider throttle_max si présent
    if 'throttle_max' in data:
        try:
            throttle_max = float(data['throttle_max'])
            if not 0.0 <= throttle_max <= 0.5:
                return False, f"Throttle_max {throttle_max} out of range [0.0, 0.5]"
        except (ValueError, TypeError):
            return False, "Throttle_max must be a number"
    
    return True, ""


def clamp_value(value: float, min_val: float, max_val: float) -> float:
    """Limite une valeur entre min et max."""
    return max(min_val, min(max_val, value))


# --- ENCODAGE MESSAGES ---

def encode_control_message(
    source: str,
    throttle: float,
    steering: float,
    throttle_max: Optional[float] = None,
    commands: Optional[List[str]] = None,
    sequence: int = 0
) -> str:
    """
    Crée un message de contrôle JSON.
    
    Args:
        source: ID du client émetteur
        throttle: Puissance moteur (-1.0 à 1.0)
        steering: Direction (-1.0 à 1.0)
        throttle_max: Puissance maximale optionnelle (0.0 à 0.5)
        commands: Liste de commandes ponctuelles
        sequence: Numéro de séquence du message
        
    Returns:
        Message JSON encodé en string
    """
    # Clamper les valeurs pour sécurité
    throttle = clamp_value(throttle, -1.0, 1.0)
    steering = clamp_value(steering, -1.0, 1.0)
    
    data = {
        'throttle': round(throttle, 3),
        'steering': round(steering, 3)
    }
    
    if throttle_max is not None:
        data['throttle_max'] = clamp_value(throttle_max, 0.0, 0.5)
    
    message = {
        'version': PROTOCOL_VERSION,
        'timestamp': time.time(),
        'source': source,
        'type': MessageType.CONTROL,
        'data': data,
        'commands': commands or [],
        'sequence': sequence
    }
    
    return json.dumps(message)


def create_heartbeat_message(source: str, sequence: int = 0) -> str:
    """
    Crée un message heartbeat (keep-alive).
    
    Args:
        source: ID du client émetteur
        sequence: Numéro de séquence
        
    Returns:
        Message JSON encodé
    """
    message = {
        'version': PROTOCOL_VERSION,
        'timestamp': time.time(),
        'source': source,
        'type': MessageType.HEARTBEAT,
        'sequence': sequence
    }
    
    return json.dumps(message)


def create_telemetry_message(
    current_throttle: float,
    current_steering: float,
    throttle_max: float,
    battery_voltage: Optional[float] = None,
    battery_current: Optional[float] = None,
    connection_status: str = "ok",
    active_client: Optional[str] = None,
    uptime: float = 0.0
) -> str:
    """
    Crée un message de télémétrie.
    
    Args:
        current_throttle: Throttle actuel
        current_steering: Steering actuel
        throttle_max: Puissance max configurée
        battery_voltage: Tension batterie (V)
        battery_current: Courant batterie (A)
        connection_status: État connexion ("ok", "degraded", "lost")
        active_client: ID du client actif
        uptime: Temps depuis démarrage serveur (s)
        
    Returns:
        Message JSON encodé
    """
    message = {
        'version': PROTOCOL_VERSION,
        'timestamp': time.time(),
        'type': MessageType.TELEMETRY,
        'data': {
            'current_throttle': round(current_throttle, 3),
            'current_steering': round(current_steering, 3),
            'throttle_max': round(throttle_max, 2),
            'battery_voltage': round(battery_voltage, 2) if battery_voltage else None,
            'battery_current': round(battery_current, 2) if battery_current else None,
            'connection_status': connection_status,
            'active_client': active_client,
            'uptime': round(uptime, 1)
        }
    }
    
    return json.dumps(message)


def create_error_message(error_text: str, source: str = "server") -> str:
    """
    Crée un message d'erreur.
    
    Args:
        error_text: Description de l'erreur
        source: Émetteur du message
        
    Returns:
        Message JSON encodé
    """
    message = {
        'version': PROTOCOL_VERSION,
        'timestamp': time.time(),
        'source': source,
        'type': MessageType.ERROR,
        'error': error_text
    }
    
    return json.dumps(message)


# --- DÉCODAGE MESSAGES ---

def decode_message(json_string: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Décode un message JSON reçu.
    
    Args:
        json_string: Message JSON brut
        
    Returns:
        Tuple (message_dict, error_string)
        Si erreur: (None, error_message)
        Si succès: (message_dict, None)
    """
    try:
        message = json.loads(json_string)
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"
    
    # Vérifier version
    if 'version' not in message:
        return None, "Missing 'version' field"
    
    if message['version'] != PROTOCOL_VERSION:
        return None, f"Unsupported protocol version: {message['version']}"
    
    # Vérifier type
    if 'type' not in message:
        return None, "Missing 'type' field"
    
    try:
        msg_type = MessageType(message['type'])
    except ValueError:
        return None, f"Unknown message type: {message['type']}"
    
    # Validation spécifique selon le type
    if msg_type == MessageType.CONTROL:
        if 'data' not in message:
            return None, "Control message missing 'data' field"
        
        is_valid, error = validate_control_data(message['data'])
        if not is_valid:
            return None, f"Invalid control data: {error}"
    
    return message, None


# --- HELPERS ---

def extract_control_data(message: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    Extrait les données de contrôle d'un message décodé.
    
    Args:
        message: Message décodé
        
    Returns:
        Dict avec throttle, steering, throttle_max ou None si invalide
    """
    if message.get('type') != MessageType.CONTROL:
        return None
    
    data = message.get('data', {})
    result = {
        'throttle': float(data.get('throttle', 0.0)),
        'steering': float(data.get('steering', 0.0))
    }
    
    if 'throttle_max' in data:
        result['throttle_max'] = float(data['throttle_max'])
    
    return result


def extract_commands(message: Dict[str, Any]) -> List[str]:
    """
    Extrait la liste de commandes d'un message.
    
    Args:
        message: Message décodé
        
    Returns:
        Liste de commandes (peut être vide)
    """
    return message.get('commands', [])


def get_message_source(message: Dict[str, Any]) -> Optional[str]:
    """Retourne l'ID de la source du message."""
    return message.get('source')


def get_message_timestamp(message: Dict[str, Any]) -> Optional[float]:
    """Retourne le timestamp du message."""
    return message.get('timestamp')


def get_message_sequence(message: Dict[str, Any]) -> int:
    """Retourne le numéro de séquence du message."""
    return message.get('sequence', 0)


# --- TESTS UNITAIRES (si lancé directement) ---

if __name__ == "__main__":
    print("=== Test du protocole Robocar ===\n")
    
    # Test 1: Créer et décoder un message de contrôle
    print("Test 1: Message de contrôle")
    msg = encode_control_message(
        source="gamepad_001",
        throttle=0.5,
        steering=-0.3,
        commands=["horn"],
        sequence=42
    )
    print(f"Encodé: {msg}")
    
    decoded, error = decode_message(msg)
    if error:
        print(f"❌ Erreur: {error}")
    else:
        print(f"✅ Décodé: {decoded}")
        control = extract_control_data(decoded)
        print(f"   Contrôle: {control}")
        print(f"   Commandes: {extract_commands(decoded)}")
    
    # Test 2: Validation avec valeurs hors limites
    print("\nTest 2: Validation valeurs hors limites")
    msg_invalid = encode_control_message(
        source="test",
        throttle=2.0,  # Sera clampé à 1.0
        steering=-5.0  # Sera clampé à -1.0
    )
    decoded, error = decode_message(msg_invalid)
    if error:
        print(f"❌ Erreur: {error}")
    else:
        control = extract_control_data(decoded)
        print(f"✅ Valeurs clampées: {control}")
    
    # Test 3: Message de télémétrie
    print("\nTest 3: Message de télémétrie")
    telem = create_telemetry_message(
        current_throttle=0.48,
        current_steering=-0.28,
        throttle_max=0.3,
        battery_voltage=11.8,
        battery_current=2.3,
        active_client="gamepad_001",
        uptime=123.4
    )
    print(f"Télémétrie: {telem}")
    
    # Test 4: Message heartbeat
    print("\nTest 4: Message heartbeat")
    hb = create_heartbeat_message(source="client_001", sequence=100)
    print(f"Heartbeat: {hb}")
    
    # Test 5: JSON invalide
    print("\nTest 5: JSON invalide")
    decoded, error = decode_message("{invalid json")
    if error:
        print(f"✅ Erreur détectée: {error}")
    else:
        print(f"❌ Devrait avoir une erreur")
    
    print("\n=== Tests terminés ===")
