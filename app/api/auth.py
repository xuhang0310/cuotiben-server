import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.user import (
    UserCreate, UserUpdate, UserLogin, UserResponse,
    Token, PasswordResetRequest, PasswordReset, EmailVerification
)
from app.services.user import (
    authenticate_user, create_user, get_user_by_email, get_user_by_id,
    update_user, generate_verification_code, store_verification_code,
    verify_email_code, request_password_reset, reset_password, create_access_token
)
from app.utils.email_service import send_verification_email
from app.core.config import settings
from datetime import timedelta
from typing import Optional
from jose import jwt

logger = logging.getLogger(__name__)

# OAuth2 scheme for JWT
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Import TokenData after defining the dependencies to avoid circular imports
from app.schemas.user import TokenData

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Register a new user with email verification"""
    logger.info(f"Starting registration process for email: {user.email}")
    
    # Check if user already exists
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        logger.warning(f"Registration attempted for already existing email: {user.email}")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password length before proceeding
    if len(user.password) > 128:
        logger.warning(f"Password for user {user.email} is very long ({len(user.password)} characters)")
        raise HTTPException(
            status_code=400, 
            detail="Password is too long. Maximum recommended length is 128 characters."
        )
    
    # Generate verification code
    #verification_code = generate_verification_code()
    verification_code = 123456
    
    # Store the verification code
    store_verification_code(user.email, verification_code)
    
    # Send verification email in background
    logger.info(f"Scheduling verification email for: {user.email}")
    background_tasks.add_task(send_verification_email, user.email, verification_code)
    
    # Return success message (user will be created after verification)
    logger.info(f"Verification code sent to {user.email}")
    raise HTTPException(status_code=200, detail=f"Verification code sent to {user.email}")


@router.post("/verify-and-register", response_model=UserResponse)
def verify_and_register_user(user: UserCreate, verification_data: EmailVerification, db: Session = Depends(get_db)):
    """Verify email with code and create user account in one step"""
    logger.info(f"Starting verify and register process for email: {verification_data.email}")
    
    # Verify the email code
    logger.info(f"Verifying email code for: {verification_data.email}")
    if not verify_email_code(verification_data.email, verification_data.verification_code):
        logger.warning(f"Invalid or expired verification code for email: {verification_data.email}")
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    else:
        logger.info(f"Successfully verified email code for: {verification_data.email}")
    
    # Check if user already exists
    logger.info(f"Checking if user already exists for email: {verification_data.email}")
    existing_user = get_user_by_email(db, verification_data.email)
    if existing_user:
        logger.warning(f"User already exists for email: {verification_data.email}")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password length before creating user
    if len(user.password) > 128:
        logger.warning(f"Password for user {verification_data.email} is very long ({len(user.password)} characters)")
        raise HTTPException(
            status_code=400, 
            detail="Password is too long. Maximum recommended length is 128 characters."
        )
    
    # Create the user
    logger.info(f"Creating user account for: {verification_data.email}")
    try:
        db_user = create_user(db, user)
        logger.info(f"Successfully created user account for: {verification_data.email}")
        return db_user
    except ValueError as e:
        logger.error(f"ValueError during user creation for {verification_data.email}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during user creation for {verification_data.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during user registration")


# Separate endpoint for requesting verification code
@router.post("/request-verification-code")
def request_verification_code(request_data: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Request a new verification code for an email"""
    email = request_data.get("email")
    logger.info(f"Received request for verification code for email: {email}")
    
    if not email:
        logger.warning("Email is required but not provided")
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Check if user already exists
    existing_user = get_user_by_email(db, email)
    if existing_user:
        logger.warning(f"Attempt to request verification code for already registered email: {email}")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate and store verification code
    #verification_code = generate_verification_code()
    verification_code = 123456
    logger.info(f"Generated verification code for email: {email}")
    store_verification_code(email, verification_code)
    
    # Send verification email in background
    logger.info(f"Scheduling verification email for: {email}")
    background_tasks.add_task(send_verification_email, email, verification_code)
    
    logger.info(f"Verification code request completed for: {email}")
    return {"message": f"Verification code sent to {email}"}


# Login endpoint
@router.post("/login", response_model=Token)
def login_user(user_login: UserLogin, db: Session = Depends(get_db)):
    """Login user with email and password"""
    logger.info(f"Login attempt for email: {user_login.email}")
    
    # Validate password length before attempting authentication
    if len(user_login.password) > 128:
        logger.warning(f"Login attempt with very long password ({len(user_login.password)} chars) for email: {user_login.email}")
        raise HTTPException(
            status_code=400, 
            detail="Password is too long. Maximum recommended length is 128 characters."
        )
    
    user = authenticate_user(db, user_login.email, user_login.password)
    if not user:
        logger.info(f"Login failed for email: {user_login.email} - incorrect email or password")
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"Login successful for email: {user_login.email}")
    
    # Create access token
    access_token_data = {"sub": user.email}
    access_token = create_access_token(
        data=access_token_data,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    logger.info(f"Access token generated for email: {user_login.email}")
    return {"access_token": access_token, "token_type": "bearer"}


# JWT authentication helper
def get_current_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from app.services.user import get_current_user
    return get_current_user(token, db)


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: UserResponse = Depends(get_current_user_from_token)):
    """Get current user info"""
    return current_user


# Request password reset
@router.post("/forgot-password")
def forgot_password(password_reset_request: PasswordResetRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Request password reset"""
    success = request_password_reset(db, password_reset_request.email)
    if not success:
        # Don't reveal if email exists to prevent enumeration attacks
        return {"message": "If email exists, a reset link has been sent"}
    
    return {"message": "If email exists, a reset link has been sent"}


# Reset password
@router.post("/reset-password")
def reset_user_password(password_reset: PasswordReset, db: Session = Depends(get_db)):
    """Reset user password with token"""
    success = reset_password(db, password_reset.token, password_reset.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    return {"message": "Password reset successfully"}


# Update user profile
@router.put("/profile", response_model=UserResponse)
def update_profile(
    user_update: UserUpdate,
    current_user: UserResponse = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    updated_user = update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user