"""Email service with pluggable providers (SMTP, Resend, SendGrid, etc).

Implements strategy pattern for email providers - easily swap implementations
without changing caller code.
"""
import smtplib
import socket
from abc import ABC, abstractmethod
from email.message import EmailMessage

from src.config.settings import (
    EMAIL_PROVIDER,
    RESEND_API_KEY,
    RESEND_FROM_EMAIL,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASS
)
from src.utils.logger import log_error


class EmailProvider(ABC):
    """Abstract base for email service providers."""

    @abstractmethod
    def send(
        self,
        email: str,
        subject: str,
        body: str,
        sender_name: str | None = None
    ) -> None:
        """Send email via provider.

        Args:
            email: Recipient email address.
            subject: Email subject.
            body: Email body (HTML).
            sender_name: Sender display name (optional).

        Raises:
            RuntimeError: If email sending fails.
        """
        pass


class ResendEmailProvider(EmailProvider):
    """Email service via Resend API (recommended for Railway)."""

    def __init__(self):
        """Initialize Resend provider with API key from settings."""
        if not RESEND_API_KEY:
            raise RuntimeError(
                "RESEND_API_KEY not set. Required for Resend provider."
            )

    def send(
        self,
        email: str,
        subject: str,
        body: str,
        sender_name: str | None = None
    ) -> None:
        """Send email via Resend API."""
        try:
            import resend

            resend.api_key = RESEND_API_KEY

            from_addr = (
                f"{sender_name} <{RESEND_FROM_EMAIL}>"
                if sender_name
                else RESEND_FROM_EMAIL
            )

            response = resend.Emails.send({
                "from": from_addr,
                "to": email,
                "subject": subject,
                "html": body
            })

            if response.get("id"):
                return  # Success

            error_msg = response.get("message", "Unknown error")
            raise RuntimeError(f"Resend API error: {error_msg}")

        except ImportError:
            raise RuntimeError("resend package not installed")
        except Exception as e:
            log_error(f"Resend send failed: {str(e)}")
            raise RuntimeError(f"Resend email failed: {str(e)}") from e


class SMTPEmailProvider(EmailProvider):
    """Email service via SMTP (Gmail, Yandex, custom SMTP servers)."""

    def __init__(self):
        """Initialize SMTP provider from settings."""
        if not all([SMTP_HOST, SMTP_USER, SMTP_PASS]):
            raise RuntimeError(
                "SMTP_HOST, SMTP_USER, SMTP_PASS required for SMTP provider"
            )
        
        self.host = SMTP_HOST
        self.port = SMTP_PORT
        self.user = SMTP_USER
        self.password = SMTP_PASS

    def send(
        self,
        email: str,
        subject: str,
        body: str,
        sender_name: str | None = None
    ) -> None:
        """Send email via SMTP."""
        try:
            msg = EmailMessage()
            msg['Subject'] = str(subject)
            if sender_name:
                msg['From'] = f"{str(sender_name)} <{self.user}>"
            else:
                msg['From'] = self.user
            msg['To'] = email
            msg.set_content(str(body), subtype='html')

            timeout = 10

            if self.port == 465:
                with smtplib.SMTP_SSL(
                    self.host,
                    self.port,
                    timeout=timeout
                ) as smtp:
                    smtp.login(self.user, self.password)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP(
                    self.host,
                    self.port,
                    timeout=timeout
                ) as smtp:
                    smtp.starttls()
                    smtp.login(self.user, self.password)
                    smtp.send_message(msg)

        except socket.timeout:
            error_msg = f"SMTP timeout ({self.host}:{self.port})"
            log_error(error_msg)
            raise RuntimeError(error_msg)
        except socket.gaierror as e:
            error_msg = f"SMTP host not found: {self.host}"
            log_error(error_msg)
            raise RuntimeError(error_msg) from e
        except ConnectionRefusedError as e:
            error_msg = f"SMTP refused ({self.host}:{self.port})"
            log_error(error_msg)
            raise RuntimeError(error_msg) from e
        except OSError as e:
            error_msg = f"Network error: {str(e)}"
            log_error(error_msg)
            raise RuntimeError(error_msg) from e
        except smtplib.SMTPAuthenticationError as e:
            error_msg = "SMTP auth failed - check SMTP_USER, SMTP_PASS"
            log_error(error_msg)
            raise RuntimeError(error_msg) from e
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            log_error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            log_error(error_msg)
            raise RuntimeError(error_msg) from e


class EmailServiceFactory:
    """Factory for creating email provider instances."""

    _providers = {
        "resend": ResendEmailProvider,
        "smtp": SMTPEmailProvider,
    }

    @staticmethod
    def get_provider() -> EmailProvider:
        """Get email provider from settings.EMAIL_PROVIDER.

        Defaults to SMTP if not set.

        Returns:
            Configured EmailProvider instance.

        Raises:
            RuntimeError: If provider not found or config invalid.
        """
        provider_name = EMAIL_PROVIDER.lower()

        if provider_name not in EmailServiceFactory._providers:
            raise RuntimeError(
                f"Unknown EMAIL_PROVIDER: {provider_name}. "
                f"Supported: {list(EmailServiceFactory._providers.keys())}"
            )

        provider_class = EmailServiceFactory._providers[provider_name]
        return provider_class()

    @staticmethod
    def register_provider(
        name: str,
        provider_class: type[EmailProvider]
    ) -> None:
        """Register custom email provider.

        Usage:
            class CustomProvider(EmailProvider): ...
            EmailServiceFactory.register_provider("custom", CustomProvider)
        """
        EmailServiceFactory._providers[name.lower()] = provider_class


def send_email(
    email: str,
    subject: str,
    body: str,
    sender_name: str | None = None
) -> None:
    """Send email using configured provider.

    Auto-selects provider from EMAIL_PROVIDER environment variable.

    Args:
        email: Recipient email address.
        subject: Email subject.
        body: Email body (HTML).
        sender_name: Sender display name (optional).

    Raises:
        RuntimeError: If email sending fails.
    """
    provider = EmailServiceFactory.get_provider()
    provider.send(email, subject, body, sender_name)
