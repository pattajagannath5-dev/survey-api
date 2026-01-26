from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt  # This is PyJWT
from jwt.exceptions import InvalidTokenError, DecodeError, ExpiredSignatureError
import httpx
from typing import Optional
from functools import lru_cache
import json

from app.config import settings

security = HTTPBearer()

# Clerk JWKS URL
CLERK_JWKS_URL = "https://api.clerk.com/v1/jwks"

@lru_cache(maxsize=1)
def get_clerk_public_keys():
    """Fetch and cache Clerk's public keys."""
    try:
        response = httpx.get(CLERK_JWKS_URL, headers={
            "Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"
        })
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching JWKS: {e}")
        return None

def get_public_key_from_jwks(token: str):
    """Get the public key from JWKS that matches the token's kid."""
    try:
        # Get the key ID from the token header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        jwks = get_clerk_public_keys()
        if not jwks:
            return None
            
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                from jwt.algorithms import RSAAlgorithm
                return RSAAlgorithm.from_jwk(json.dumps(key))
        
        return None
    except Exception as e:
        print(f"Error getting public key: {e}")
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract and validate user ID from Clerk JWT token."""
    token = credentials.credentials
    
    try:
        # For development/testing with Clerk, we can decode without verification
        # In production, you should verify with the public key
        if settings.DEBUG:
            # Decode without verification for development
            payload = jwt.decode(token, options={"verify_signature": False})
        else:
            # Production: verify with Clerk's public key
            public_key = get_public_key_from_jwks(token)
            if not public_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials - invalid key",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_aud": False}
            )
        
        # Clerk stores user ID in 'sub' claim
        user_id: Optional[str] = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials - no user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_id
        
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (DecodeError, InvalidTokenError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[str]:
    """Optional authentication - returns None if not authenticated."""
    if credentials is None:
        return None
    
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None
