# app/auth/routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import List
from app.auth.models import (
    User, UserCreate, UserLogin, UserUpdate, Token, 
    PasswordReset, PasswordChange
)
from app.auth.service import AuthService
from app.auth.dependencies import (
    get_current_user, get_current_active_user, 
    get_current_admin_user, get_current_recruiter_user
)
from app.auth.utils import get_token_expiration
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends()
):
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        auth_service: Authentication service
        
    Returns:
        User: The created user
        
    Raises:
        HTTPException: If user already exists or validation fails
    """
    try:
        user = await auth_service.create_user(user_data)
        logger.info(f"New user registered: {user.email}")
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/login", response_model=Token)
async def login_user(
    user_credentials: UserLogin,
    auth_service: AuthService = Depends()
):
    """
    Login user and return access token.
    
    Args:
        user_credentials: User login credentials
        auth_service: Authentication service
        
    Returns:
        Token: Access token and user information
        
    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        user = await auth_service.authenticate_user(
            user_credentials.email, 
            user_credentials.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Create access token
        access_token = auth_service.create_access_token_for_user(user)
        expires_in = int((get_token_expiration() - user.created_at).total_seconds())
        
        logger.info(f"User logged in: {user.email}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current user information
    """
    return current_user

@router.put("/me", response_model=User)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends()
):
    """
    Update current user information.
    
    Args:
        user_data: User update data
        current_user: Current authenticated user
        auth_service: Authentication service
        
    Returns:
        User: Updated user information
        
    Raises:
        HTTPException: If update fails
    """
    try:
        updated_user = await auth_service.update_user(current_user.id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User updated: {current_user.email}")
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends()
):
    try:
        await auth_service.change_password(current_user.id, password_data.current_password, password_data.new_password)
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to change password")

# Admin-only routes
@router.get("/users", response_model=List[User])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    auth_service: AuthService = Depends()
):
    """
    List all users (admin only).
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        current_user: Current authenticated admin user
        auth_service: Authentication service
        
    Returns:
        List[User]: List of users
    """
    try:
        users = await auth_service.list_users(skip=skip, limit=limit)
        return users
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_admin_user),
    auth_service: AuthService = Depends()
):
    """
    Get user by ID (admin only).
    
    Args:
        user_id: User ID
        current_user: Current authenticated admin user
        auth_service: Authentication service
        
    Returns:
        User: User information
        
    Raises:
        HTTPException: If user not found
    """
    try:
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    auth_service: AuthService = Depends()
):
    """
    Update user (admin only).
    
    Args:
        user_id: User ID
        user_data: User update data
        current_user: Current authenticated admin user
        auth_service: Authentication service
        
    Returns:
        User: Updated user information
        
    Raises:
        HTTPException: If update fails
    """
    try:
        updated_user = await auth_service.update_user(user_id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User updated by admin: {updated_user.email}")
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_admin_user),
    auth_service: AuthService = Depends()
):
    """
    Delete user (admin only).
    
    Args:
        user_id: User ID
        current_user: Current authenticated admin user
        auth_service: Authentication service
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        success = await auth_service.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User deleted by admin: {user_id}")
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 