"""Authentication router for login, registration, and token management."""

from fastapi import APIRouter, HTTPException, status

from app.api.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.services.auth_service import get_auth_service
from app.services.user_service import get_user_service
from app.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """Login endpoint for user authentication.

    Args:
        request: Login credentials (username and password).

    Returns:
        LoginResponse with JWT token and user information.

    Raises:
        HTTPException: If authentication fails.
    """
    logger.info(f"Login attempt for user: {request.username}")

    user_service = get_user_service()
    auth_service = get_auth_service()

    # Authenticate user
    user = user_service.authenticate_user(request.username, request.password)
    if not user:
        logger.debug(f"Login failed for user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Create JWT token
    access_token = auth_service.create_access_token(
        user_id=user.user_id,
        username=user.username,
        role=user.role,
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.user_id,
        username=user.username,
        role=user.role,
    )


@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest) -> RegisterResponse:
    """Register endpoint for user registration.

    Args:
        request: Registration details.

    Returns:
        RegisterResponse with user information.

    Raises:
        HTTPException: If registration fails.
    """
    logger.info(f"Registration attempt for user: {request.username}")

    user_service = get_user_service()

    # Create user
    user = user_service.create_user(
        username=request.username,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        role="user",
    )

    if not user:
        logger.warning(f"Registration failed for user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. User may already exist.",
        )

    return RegisterResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
    )


@router.post("/change-password")
async def change_password(request: ChangePasswordRequest) -> dict:
    """Change password endpoint.

    Args:
        request: Current and new password.

    Returns:
        Dictionary with success message.

    Raises:
        HTTPException: If password change fails.
    """
    auth_service = get_auth_service()

    # Validate new password confirmation
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation do not match",
        )

    # Validate old password is different from new
    if request.old_password == request.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from old password",
        )

    logger.info("Password change request received")

    return {"message": "Password change functionality requires authenticated user context"}


@router.get("/verify-token")
async def verify_token(token: str) -> dict:
    """Verify JWT token validity.

    Args:
        token: JWT token to verify.

    Returns:
        Dictionary with token validity and decoded data.
    """
    auth_service = get_auth_service()

    token_data = auth_service.verify_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return {
        "valid": True,
        "username": token_data.sub,
        "user_id": token_data.user_id,
        "role": token_data.role,
    }
