from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.http import HTTPBase
from jose import jwt
from app.core.config import settings
from app.services.user import verify_token
from app.schemas.user import TokenData
from app.services.user import get_user_by_email
from typing import Optional

import logging
logger = logging.getLogger(__name__)
class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: Optional[HTTPAuthorizationCredentials] = await super(JWTBearer, self).__call__(request)
        
        if credentials is None:
            logger.error(f"Authentication failed: No credentials provided. Headers: {request.headers}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if not credentials.credentials:
            logger.error("Authentication failed: Credentials object exists but token is empty.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = credentials.credentials
        logger.info(f"Validating JWT token: {token[:10]}...")

        # Verify the token
        payload = verify_token(token)
        if payload is None:
            logger.error("Authentication failed: Token verification failed (payload is None).")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        email: str = payload.get("sub")
        if email is None:
            logger.error("Authentication failed: 'sub' claim (email) not found in token payload.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_data = TokenData(email=email)
        return token_data