"""Authentication service for user authentication and token management."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from app.models.user import TokenData
from app.utils.logger import logger
from app.utils.settings import settings

# Password context for hashing - use pbkdf2 as primary, bcrypt as fallback
# pbkdf2 is more compatible and doesn't have the version detection issues
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
    pbkdf2_sha256__default_rounds=30000,  # Strong but reasonable rounds
)

# Note: CryptContext automatically upgrades hashes to the preferred scheme
# when verify() succeeds. Existing bcrypt hashes will be upgraded to pbkdf2
# on successful login.
# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours


class AuthenticationService:
    """Service for handling authentication operations."""

    def __init__(self, secret_key: Optional[str] = None):
        """Initialize authentication service.

        Args:
            secret_key: JWT secret key. If None, loads from settings.
        """
        self.secret_key = secret_key or self._get_secret_key()

    @staticmethod
    def _get_secret_key() -> str:
        """Get JWT secret key from settings.

        Returns:
            JWT secret key.

        Raises:
            ValueError: If JWT_SECRET_KEY not configured.
        """
        try:
            return settings.JWT_SECRET_KEY
        except AttributeError:
            raise ValueError(
                "JWT_SECRET_KEY not configured. Set JWT_SECRET_KEY environment variable."
            )

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using pbkdf2_sha256.

        Args:
            password: Plain text password.

        Returns:
            Hashed password.
        """
        try:
            return pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Password hashing error: {type(e).__name__}: {e}")
            raise ValueError(f"Password hashing failed: {e}")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.

        Args:
            plain_password: Plain text password.
            hashed_password: Hashed password to verify against.

        Returns:
            True if password matches, False otherwise.
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            # Log password verification errors at debug level to reduce noise
            logger.debug(f"Password verification error: {type(e).__name__}: {e}")
            return False

    def create_access_token(
        self,
        user_id: str,
        username: str,
        role: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a JWT access token.

        Args:
            user_id: User ID.
            username: Username.
            role: User role.
            expires_delta: Optional expiration time delta. Defaults to 24 hours.

        Returns:
            Encoded JWT token.
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        expire = datetime.now(timezone.utc) + expires_delta
        to_encode = {
            "sub": username,
            "user_id": user_id,
            "role": role,
            "exp": expire,
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=ALGORITHM)
        logger.info(f"Created access token for user: {username}")
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode a JWT token.

        Args:
            token: JWT token to verify.

        Returns:
            TokenData if valid, None if invalid.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            role: str = payload.get("role")

            if username is None or user_id is None:
                logger.warning("Token missing required claims")
                return None

            token_data = TokenData(sub=username, user_id=user_id, role=role)
            return token_data
        except JWTError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except ValidationError as e:
            logger.warning(f"Token validation error: {e}")
            return None

    def decode_token(self, token: str) -> Optional[dict]:
        """Decode a JWT token without full validation.

        Args:
            token: JWT token to decode.

        Returns:
            Decoded payload if valid, None otherwise.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning(f"Failed to decode token: {e}")
            return None


# Global singleton instance
_auth_service: Optional[AuthenticationService] = None


def get_auth_service() -> AuthenticationService:
    """Get or create the global authentication service.

    Returns:
        AuthenticationService instance.
    """
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthenticationService()
    return _auth_service


def initialize_auth_service(secret_key: Optional[str] = None) -> AuthenticationService:
    """Initialize the global authentication service.

    Args:
        secret_key: Optional JWT secret key.

    Returns:
        Initialized AuthenticationService instance.
    """
    global _auth_service
    _auth_service = AuthenticationService(secret_key=secret_key)
    return _auth_service
