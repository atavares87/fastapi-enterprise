"""
Security utilities for authentication and authorization.

This module provides JWT token handling, password hashing, and other
security-related utilities for the application.
"""

from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt  # type: ignore[import-untyped]
from passlib.context import CryptContext  # type: ignore[import-untyped]
from structlog import get_logger

from app.core.config import get_settings

settings = get_settings()

# Initialize logger
logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityManager:
    """
    Handles security operations including JWT tokens and password hashing.

    This class provides methods for creating and verifying JWT tokens,
    hashing and verifying passwords, and other security operations.
    """

    def __init__(self) -> None:
        """Initialize security manager with application settings."""
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_minutes = settings.REFRESH_TOKEN_EXPIRE_MINUTES

    def create_access_token(
        self,
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create JWT access token.

        Args:
            data: Claims to include in the token
            expires_delta: Custom expiration time (optional)

        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()

        # Set expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )

        # Add standard claims
        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "access",
            }
        )

        # Encode token
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm,
        )

        logger.info(
            "Access token created",
            subject=data.get("sub"),
            expires_at=expire.isoformat(),
        )

        return str(encoded_jwt)

    def create_refresh_token(
        self,
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create JWT refresh token.

        Args:
            data: Claims to include in the token
            expires_delta: Custom expiration time (optional)

        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()

        # Set expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.refresh_token_expire_minutes
            )

        # Add standard claims
        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "refresh",
            }
        )

        # Encode token
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm,
        )

        logger.info(
            "Refresh token created",
            subject=data.get("sub"),
            expires_at=expire.isoformat(),
        )

        return str(encoded_jwt)

    def verify_token(
        self,
        token: str,
        token_type: str = "access",  # nosec B107 - This is a token type, not a password
    ) -> dict[str, Any] | None:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token string to verify
            token_type: Expected token type ('access' or 'refresh')

        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )

            # Verify token type
            if payload.get("type") != token_type:
                logger.warning(
                    "Invalid token type",
                    expected=token_type,
                    actual=payload.get("type"),
                )
                return None

            # Check expiration
            exp = payload.get("exp")
            if exp is None or datetime.utcnow().timestamp() > exp:
                logger.warning("Token expired")
                return None

            logger.debug(
                "Token verified successfully",
                subject=payload.get("sub"),
                token_type=token_type,
            )

            return dict(payload)

        except JWTError as e:
            logger.warning("JWT verification failed", error=str(e))
            return None
        except Exception as e:
            logger.error("Token verification error", error=str(e))
            return None

    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt.

        Args:
            password: Plain text password to hash

        Returns:
            Hashed password string
        """
        hashed = pwd_context.hash(password)
        logger.debug("Password hashed successfully")
        return str(hashed)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to verify against

        Returns:
            True if password matches, False otherwise
        """
        try:
            is_valid = pwd_context.verify(plain_password, hashed_password)
            if is_valid:
                logger.debug("Password verification successful")
            else:
                logger.warning("Password verification failed")
            return bool(is_valid)
        except Exception as e:
            logger.error("Password verification error", error=str(e))
            return False

    def generate_password_reset_token(self, email: str) -> str:
        """
        Generate password reset token.

        Args:
            email: Email address for password reset

        Returns:
            Password reset token
        """
        data = {"email": email, "type": "password_reset"}
        expires_delta = timedelta(hours=1)  # Reset tokens expire in 1 hour

        return self.create_access_token(data, expires_delta)

    def verify_password_reset_token(self, token: str) -> str | None:
        """
        Verify password reset token and extract email.

        Args:
            token: Password reset token to verify

        Returns:
            Email address if token is valid, None otherwise
        """
        payload = self.verify_token(token, "access")
        if payload and payload.get("type") == "password_reset":
            return str(payload.get("email")) if payload.get("email") else None
        return None


# Global security manager instance
security = SecurityManager()


def get_security_manager() -> SecurityManager:
    """
    Get security manager instance.

    This function can be used as a FastAPI dependency to inject
    the security manager into route handlers.

    Returns:
        SecurityManager instance
    """
    return security


# Convenience functions
def create_access_token(data: dict[str, Any]) -> str:
    """Create access token using global security manager."""
    return security.create_access_token(data)


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create refresh token using global security manager."""
    return security.create_refresh_token(data)


def verify_token(
    token: str, token_type: str = "access"
) -> dict[str, Any] | None:  # nosec B107 - This is a token type, not a password
    """Verify token using global security manager."""
    return security.verify_token(token, token_type)


def hash_password(password: str) -> str:
    """Hash password using global security manager."""
    return security.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using global security manager."""
    return security.verify_password(plain_password, hashed_password)
