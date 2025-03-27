"""Slack bot utility for sending messages and notifications."""

import os
import requests
from typing import Optional
from loguru import logger
from dotenv import load_dotenv

class SlackBot:
    """Utility class for sending messages to Slack via webhooks."""
    
    def __init__(self):
        load_dotenv()
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not found in environment variables")
            
    def send_message(self, channel: str, message: str, thread_ts: Optional[str] = None) -> bool:
        """
        Send a message to a Slack channel.
        
        Args:
            channel: The channel to send the message to
            message: The message content
            thread_ts: Optional timestamp of parent message for threading
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if not self.webhook_url:
            logger.error("Cannot send message: SLACK_WEBHOOK_URL not configured")
            return False
            
        try:
            payload = {
                "channel": channel,
                "text": message,
                "unfurl_links": True,
                "unfurl_media": True
            }
            
            if thread_ts:
                payload["thread_ts"] = thread_ts
                
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully sent message to channel {channel}")
                return True
            else:
                logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message to Slack: {e}")
            return False
            
    def format_message(self, title: str, content: str) -> str:
        """
        Format a message with title and content.
        
        Args:
            title: The message title
            content: The message content
            
        Returns:
            str: Formatted message
        """
        return f"*{title}*\n{content}"
        
    def format_error(self, error: str) -> str:
        """
        Format an error message.
        
        Args:
            error: The error message
            
        Returns:
            str: Formatted error message
        """
        return f"❌ *Error:*\n{error}"
        
    def format_success(self, message: str) -> str:
        """
        Format a success message.
        
        Args:
            message: The success message
            
        Returns:
            str: Formatted success message
        """
        return f"✅ *Success:*\n{message}" 