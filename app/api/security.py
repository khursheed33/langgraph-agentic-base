"""Security dependencies for FastAPI."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.models.user import AuthUser, UserRole
from app.services.auth_service import get_auth_service
from app.services.user_service import get_user_service
from app.utils.logger import logger

# Security scheme for bearer tokens
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthUser:
    """Dependency to get current authenticated user from token.

    Args:
        credentials: HTTP authorization credentials (bearer token).

    Returns:
        AuthUser with user information.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    token = credentials.credentials
    auth_service = get_auth_service()
    user_service = get_user_service()

    # Verify token
    token_data = auth_service.verify_token(token)
    if not token_data:
        logger.warning("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = user_service.get_user_by_id(token_data.user_id)
    if not user:
        logger.warning(f"User not found: {token_data.user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning(f"User inactive: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return AuthUser(
        user_id=user.user_id,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        bypass_guardrails=user.bypass_guardrails,
    )


async def get_current_admin_user(
    current_user: AuthUser = Depends(get_current_user),
) -> AuthUser:
    """Dependency to ensure current user is admin.

    Args:
        current_user: Current authenticated user.

    Returns:
        AuthUser if user is admin.

    Raises:
        HTTPException: If user is not admin.
    """
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Admin access denied for user: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
