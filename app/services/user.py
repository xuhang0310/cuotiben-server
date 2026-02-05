from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
import secrets
from typing import Optional
import time
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserLogin, TokenData
from app.core.config import settings
from app.utils.email_service import send_verification_email, send_password_reset_email

# Simple in-memory store for verification codes (in production, use Redis or database)
verification_codes_store = {}
password_reset_tokens_store = {}


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify a JWT token and return the payload."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.JWTError:
        return None


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user."""
    # Hash the password
    hashed_password = get_password_hash(user.password)
    
    # Create the user object
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise ValueError("Email or username already exists")


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """Update a user's information."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def generate_verification_code(length: int = 6) -> str:
    """Generate a random verification code."""
    return ''.join(secrets.choice('0123456789') for _ in range(length))


def store_verification_code(email: str, code: str, expiry_minutes: int = 10):
    """Store the verification code with expiration time."""
    expiry_time = time.time() + (expiry_minutes * 60)
    verification_codes_store[email] = {
        'code': code,
        'expires_at': expiry_time
    }


def verify_email_code(email: str, code: str) -> bool:
    """Verify the email verification code."""
    if email not in verification_codes_store:
        return False

    stored_data = verification_codes_store[email]

    # Check if code has expired
    if time.time() > stored_data['expires_at']:
        del verification_codes_store[email]  # Clean up expired code
        return False

    # Check if code matches
    if stored_data['code'] != code:
        return False

    # Clean up the verified code
    del verification_codes_store[email]
    return True


def request_password_reset(db: Session, email: str) -> bool:
    """Request a password reset for a user."""
    user = get_user_by_email(db, email)
    if not user:
        return False

    # Generate a reset token
    reset_token = secrets.token_urlsafe(32)

    # Store the reset token with expiration (24 hours)
    expiry_time = time.time() + (24 * 60 * 60)  # 24 hours in seconds
    password_reset_tokens_store[reset_token] = {
        'email': email,
        'expires_at': expiry_time
    }

    # Send password reset email
    try:
        send_password_reset_email(email, reset_token)
        return True
    except Exception:
        return False


def reset_password(db: Session, token: str, new_password: str) -> bool:
    """Reset a user's password using a reset token."""
    # Check if token exists and is not expired
    if token not in password_reset_tokens_store:
        return False

    stored_data = password_reset_tokens_store[token]

    # Check if token has expired
    if time.time() > stored_data['expires_at']:
        del password_reset_tokens_store[token]  # Clean up expired token
        return False

    # Get the user by email from the stored data
    email = stored_data['email']
    user = get_user_by_email(db, email)

    if not user:
        del password_reset_tokens_store[token]  # Clean up invalid token
        return False

    # Hash the new password and update the user
    hashed_password = get_password_hash(new_password)
    user.password_hash = hashed_password
    db.commit()

    # Clean up the used token
    del password_reset_tokens_store[token]

    return True


def verify_and_create_user(db: Session, email: str, verification_code: str, user_create: UserCreate) -> Optional[User]:
    """Verify the email code and create the user if valid."""
    # First verify the code
    if not verify_email_code(email, verification_code):
        return None
    
    # Then create the user
    return create_user(db, user_create)