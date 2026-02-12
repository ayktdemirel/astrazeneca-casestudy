import os
from fastapi import Depends, HTTPException, status, Header
from jose import jwt, JWTError
from typing import Optional, List

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key-change-me")
ALGORITHM = "HS256"

# Role Constants
ROLE_ADMIN = "ADMIN"
ROLE_ANALYST = "ANALYST"
ROLE_EXECUTIVE = "EXECUTIVE"

class User:
    def __init__(self, email: str, role: str, user_id: str):
        self.email = email
        self.role = role
        self.user_id = user_id

async def get_current_user(authorization: str = Header(None)) -> User:
    """
    Validates the JWT token from the Authorization header and returns the user.
    Throws 401 if invalid or missing.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        user_id: str = payload.get("userId")
        
        if email is None or role is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
            
        return User(email=email, role=role, user_id=user_id)
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(allowed_roles: List[str]):
    """
    Dependency factory to check if the user has one of the allowed roles.
    """
    async def role_checker(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role {user.role}"
            )
        return user
    return role_checker
