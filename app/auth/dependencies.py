# app/auth/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.auth.models import User, TokenData, UserRole
from app.auth.utils import verify_token
from app.auth.service import AuthService
import logging

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends()
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        credentials: The HTTP authorization credentials
        auth_service: The authentication service
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify the token
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        # Extract user data from token
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        
        if user_id is None or email is None:
            raise credentials_exception
        
        token_data = TokenData(user_id=user_id, email=email, role=role)
        
        # Get user from database
        user = await auth_service.get_user_by_id(user_id)
        if user is None:
            raise credentials_exception
        
        return user
        
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}")
        raise credentials_exception

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        User: The active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current admin user.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        User: The admin user
        
    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_current_recruiter_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current recruiter user.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        User: The recruiter user
        
    Raises:
        HTTPException: If user is not a recruiter or admin
    """
    if current_user.role not in [UserRole.RECRUITER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends()
) -> Optional[User]:
    if not credentials:
        return None
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            return None
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return await auth_service.get_user_by_id(user_id)
    except Exception:
        return None 