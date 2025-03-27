"""Secure communication module for P.E.P.P.E.R."""

from typing import Dict, Any, Optional
from loguru import logger
from cryptography.fernet import Fernet
import json
import base64
import os

class SecureCommunication:
    """Handles secure communication between agents."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize secure communication.
        
        Args:
            encryption_key: Optional encryption key. If not provided, will generate one.
        """
        self.encryption_key = encryption_key or os.getenv('CORE_ENCRYPTION_KEY')
        if not self.encryption_key:
            self.encryption_key = Fernet.generate_key()
            logger.warning("No encryption key provided, generated new key")
        self.cipher_suite = Fernet(self.encryption_key.encode())
        
    def encrypt_message(self, message: Dict[str, Any]) -> str:
        """Encrypt a message.
        
        Args:
            message: Message to encrypt
            
        Returns:
            Encrypted message as base64 string
        """
        try:
            message_str = json.dumps(message)
            encrypted_data = self.cipher_suite.encrypt(message_str.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt message: {e}")
            raise
            
    def decrypt_message(self, encrypted_message: str) -> Dict[str, Any]:
        """Decrypt a message.
        
        Args:
            encrypted_message: Encrypted message as base64 string
            
        Returns:
            Decrypted message as dictionary
        """
        try:
            encrypted_data = base64.b64decode(encrypted_message.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to decrypt message: {e}")
            raise
            
    def verify_message(self, message: Dict[str, Any], signature: str) -> bool:
        """Verify message signature.
        
        Args:
            message: Message to verify
            signature: Message signature
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            message_str = json.dumps(message, sort_keys=True)
            expected_signature = self.cipher_suite.encrypt(message_str.encode())
            return signature == base64.b64encode(expected_signature).decode()
        except Exception as e:
            logger.error(f"Failed to verify message: {e}")
            return False
            
    def sign_message(self, message: Dict[str, Any]) -> str:
        """Sign a message.
        
        Args:
            message: Message to sign
            
        Returns:
            Message signature
        """
        try:
            message_str = json.dumps(message, sort_keys=True)
            signature = self.cipher_suite.encrypt(message_str.encode())
            return base64.b64encode(signature).decode()
        except Exception as e:
            logger.error(f"Failed to sign message: {e}")
            raise
