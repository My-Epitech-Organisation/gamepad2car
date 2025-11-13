"""
Core module for Robocar control system.
Contains base classes and protocol definitions.
"""

from .protocol import (
    MessageType,
    encode_control_message,
    decode_message,
    validate_control_data,
    create_telemetry_message,
    create_heartbeat_message
)

__all__ = [
    'MessageType',
    'encode_control_message',
    'decode_message',
    'validate_control_data',
    'create_telemetry_message',
    'create_heartbeat_message'
]
