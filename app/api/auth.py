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

# OAuth2 scheme for JWT
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Import TokenData after defining the dependencies to avoid circular imports
from app.schemas.user import TokenData

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Register a new user with email verification"""
    # Check if user already exists
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate verification code
    verification_code = generate_verification_code()
    
    # Store the verification code
    store_verification_code(user.email, verification_code)
    
    # Send verification email in background
    background_tasks.add_task(send_verification_email, user.email, verification_code)
    
    # Return success message (user will be created after verification)
    raise HTTPException(status_code=200, detail=f"Verification code sent to {user.email}")


@router.post("/verify-and-register", response_model=UserResponse)
def verify_and_register_user(user: UserCreate, verification_data: EmailVerification, db: Session = Depends(get_db)):
    """Verify email with code and create user account in one step"""
    # Verify the email code
    if not verify_email_code(verification_data.email, verification_data.verification_code):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    
    # Check if user already exists
    existing_user = get_user_by_email(db, verification_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create the user
    try:
        db_user = create_user(db, user)
        return db_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Separate endpoint for requesting verification code
@router.post("/request-verification-code")
def request_verification_code(request_data: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Request a new verification code for an email"""
    email = request_data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Check if user already exists
    existing_user = get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate and store verification code
    verification_code = generate_verification_code()
    store_verification_code(email, verification_code)
    
    # Send verification email in background
    background_tasks.add_task(send_verification_email, email, verification_code)
    
    return {"message": f"Verification code sent to {email}"}


# Login endpoint
@router.post("/login", response_model=Token)
def login_user(user_login: UserLogin, db: Session = Depends(get_db)):
    """Login user with email and password"""
    user = authenticate_user(db, user_login.email, user_login.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_data = {"sub": user.email}
    access_token = create_access_token(
        data=access_token_data,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# JWT authentication helper
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except jwt.JWTError:
        raise credentials_exception
    # We'll get the db session inside the function that uses this dependency
    return token_data


@router.get("/me", response_model=UserResponse)
def read_users_me(token_data: TokenData = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user info"""
    user = get_user_by_email(db, email=token_data.email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


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
    token_data: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    # Get the user by email from token data
    current_user = get_user_by_email(db, email=token_data.email)
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user