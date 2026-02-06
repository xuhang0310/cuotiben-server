from datetime import datetime, timedelta
import hashlib
import secrets
from typing import Optional
from jose import JWTError, jwt
from app.core.config import settings

# 生成盐值
def generate_salt() -> str:
    """Generate a random salt for password hashing."""
    return secrets.token_hex(16)

# 验证密码
def verify_password(plain_password: str, hashed_password: str):
    """Verify a plain password against a hashed password."""
    try:
        # Extract salt and hash from the stored hashed_password
        parts = hashed_password.split('$')
        if len(parts) != 2:
            return False
        salt, stored_hash = parts
        
        # Hash the plain password with the extracted salt
        computed_hash = hashlib.md5((plain_password + salt).encode()).hexdigest()
        
        # Compare the hashes
        return computed_hash == stored_hash
    except Exception:
        # Return False in case of any error during verification
        return False

# 获取密码哈希值
def get_password_hash(password: str):
    """Hash a plain password using MD5 with salt."""
    # Generate a salt
    salt = generate_salt()
    
    # Create the hash: MD5(password + salt)
    password_hash = hashlib.md5((password + salt).encode()).hexdigest()
    
    # Return salt and hash combined with a separator
    return f"{salt}${password_hash}"

# 创建访问令牌
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# 验证访问令牌
def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None