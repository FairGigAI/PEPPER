"""Email utility supporting multiple providers (SMTP, Mailgun, SendGrid)."""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Union
from loguru import logger
import requests
from dotenv import load_dotenv

class Emailer:
    """Email utility class supporting multiple providers."""
    
    def __init__(self):
        load_dotenv()
        self.provider = os.getenv('EMAIL_PROVIDER', 'smtp').lower()
        self.from_email = os.getenv('EMAIL_FROM')
        self.to_email = os.getenv('EMAIL_TO')
        
        if not self.from_email or not self.to_email:
            logger.warning("Email configuration incomplete")
            
        # Initialize provider-specific settings
        if self.provider == 'smtp':
            self.smtp_host = os.getenv('SMTP_HOST')
            self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
            self.smtp_username = os.getenv('SMTP_USERNAME')
            self.smtp_password = os.getenv('SMTP_PASSWORD')
            self.smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        elif self.provider == 'mailgun':
            self.mailgun_api_key = os.getenv('MAILGUN_API_KEY')
            self.mailgun_domain = os.getenv('MAILGUN_DOMAIN')
        elif self.provider == 'sendgrid':
            self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
            
    def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send an email using the configured provider.
        
        Args:
            to: Recipient email address(es)
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML version of the email body
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not self.from_email:
            logger.error("Cannot send email: EMAIL_FROM not configured")
            return False
            
        try:
            if self.provider == 'smtp':
                return self._send_smtp(to, subject, body, html_body)
            elif self.provider == 'mailgun':
                return self._send_mailgun(to, subject, body, html_body)
            elif self.provider == 'sendgrid':
                return self._send_sendgrid(to, subject, body, html_body)
            else:
                logger.error(f"Unsupported email provider: {self.provider}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
            
    def _send_smtp(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send email using SMTP."""
        if not all([self.smtp_host, self.smtp_username, self.smtp_password]):
            logger.error("SMTP configuration incomplete")
            return False
            
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to if isinstance(to, str) else ', '.join(to)
            
            msg.attach(MIMEText(body, 'plain'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
                
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
            logger.info(f"Email sent successfully via SMTP to {to}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return False
            
    def _send_mailgun(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send email using Mailgun."""
        if not all([self.mailgun_api_key, self.mailgun_domain]):
            logger.error("Mailgun configuration incomplete")
            return False
            
        try:
            url = f"https://api.mailgun.net/v3/{self.mailgun_domain}/messages"
            data = {
                "from": self.from_email,
                "to": to if isinstance(to, str) else to,
                "subject": subject,
                "text": body,
                "html": html_body
            }
            
            response = requests.post(
                url,
                auth=("api", self.mailgun_api_key),
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Email sent successfully via Mailgun to {to}")
                return True
            else:
                logger.error(f"Mailgun error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Mailgun error: {e}")
            return False
            
    def _send_sendgrid(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send email using SendGrid."""
        if not self.sendgrid_api_key:
            logger.error("SendGrid configuration incomplete")
            return False
            
        try:
            url = "https://api.sendgrid.com/v3/mail/send"
            data = {
                "personalizations": [{
                    "to": [{"email": email} for email in (to if isinstance(to, list) else [to])]
                }],
                "from": {"email": self.from_email},
                "subject": subject,
                "content": [
                    {"type": "text/plain", "value": body}
                ]
            }
            
            if html_body:
                data["content"].append({"type": "text/html", "value": html_body})
                
            response = requests.post(
                url,
                headers={"Authorization": f"Bearer {self.sendgrid_api_key}"},
                json=data,
                timeout=10
            )
            
            if response.status_code == 202:
                logger.info(f"Email sent successfully via SendGrid to {to}")
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return False 