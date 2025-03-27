"""Secure inter-agent communication module."""

import os
import json
import time
import hmac
import hashlib
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime
from loguru import logger
from pydantic import BaseModel, Field
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# Type checking imports to avoid circular dependencies
if TYPE_CHECKING:
    from .config import ConfigLoader, SystemConfig

class Message(BaseModel):
    """Secure message model for inter-agent communication."""
    sender_id: str
    receiver_id: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: float = Field(default_factory=time.time)
    nonce: str = Field(default_factory=lambda: os.urandom(16).hex())
    signature: Optional[str] = None

class SecureCommunication:
    """Handles secure communication between agents."""
    
    def __init__(
        self,
        agent_id: str,
        config: Optional['ConfigLoader'] = None,
        secret_key: Optional[str] = None
    ):
        """Initialize secure communication.
        
        Args:
            agent_id: ID of the agent
            config: Optional configuration loader
            secret_key: Optional secret key for encryption
        """
        self.agent_id = agent_id
        self.config = config
        
        # Get secret key from config or environment
        if not secret_key and self.config:
            system_config = self.config.get_system_config()
            if system_config:
                secret_key = system_config.agent_secret_key
                
        if not secret_key:
            secret_key = os.getenv("AGENT_SECRET_KEY")
            
        if not secret_key:
            secret_key = self._generate_secret_key()
            
        self.secret_key = secret_key
        self.fernet = self._setup_encryption()
        self._message_cache = {}
        
    def _generate_secret_key(self) -> str:
        """Generate a secure secret key."""
        key = Fernet.generate_key()
        return base64.urlsafe_b64encode(key).decode()
        
    def _setup_encryption(self) -> Fernet:
        """Set up encryption using Fernet."""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.secret_key.encode()))
        return Fernet(key)
        
    def _generate_signature(self, message: Message) -> str:
        """Generate HMAC signature for message."""
        message_data = f"{message.sender_id}:{message.receiver_id}:{message.message_type}:{message.timestamp}:{message.nonce}"
        return hmac.new(
            self.secret_key.encode(),
            message_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
    def _verify_signature(self, message: Message) -> bool:
        """Verify message signature."""
        if not message.signature:
            return False
        expected_signature = self._generate_signature(message)
        return hmac.compare_digest(message.signature, expected_signature)
        
    def encrypt_message(self, message: Message) -> str:
        """Encrypt a message."""
        message_dict = message.dict()
        message_dict["signature"] = self._generate_signature(message)
        return self.fernet.encrypt(json.dumps(message_dict).encode()).decode()
        
    def decrypt_message(self, encrypted_message: str) -> Message:
        """Decrypt a message."""
        try:
            decrypted_data = self.fernet.decrypt(encrypted_message.encode())
            message_dict = json.loads(decrypted_data)
            message = Message(**message_dict)
            
            if not self._verify_signature(message):
                raise ValueError("Invalid message signature")
                
            # Check for replay attacks
            if message.timestamp < time.time() - 300:  # 5 minutes
                raise ValueError("Message too old")
                
            # Check for duplicate messages
            message_key = f"{message.sender_id}:{message.nonce}"
            if message_key in self._message_cache:
                raise ValueError("Duplicate message")
            self._message_cache[message_key] = time.time()
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to decrypt message: {e}")
            raise
            
    def send_message(self, receiver_id: str, message_type: str, payload: Dict[str, Any]) -> str:
        """Send an encrypted message to another agent."""
        message = Message(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=message_type,
            payload=payload
        )
        return self.encrypt_message(message)
        
    def receive_message(self, encrypted_message: str) -> Message:
        """Receive and decrypt a message."""
        return self.decrypt_message(encrypted_message)
        
    def cleanup(self):
        """Clean up old message cache entries."""
        current_time = time.time()
        self._message_cache = {
            k: v for k, v in self._message_cache.items()
            if current_time - v < 300  # Keep only messages less than 5 minutes old
        } 