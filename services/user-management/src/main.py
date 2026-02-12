import sys
sys.path.append("/app")

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
from typing import List
import logging

from libs.shared.src.logger import setup_logger
from libs.shared.src.middleware import CorrelationIdMiddleware
from .database import get_db, engine, Base
from . import models, schemas, auth
from libs.shared.src.exceptions import setup_exception_handlers
from libs.shared.src.auth import require_role

logger = setup_logger("user-management-service")

app = FastAPI(
    title="User Management Service",
    description="Handles user registration, authentication (JWT), and role management.",
    version="1.0.0"
)

app.add_middleware(CorrelationIdMiddleware)
setup_exception_handlers(app)

# Initializer to create default admin if not exists
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Check if we need to seed a default user
    async with engine.connect() as conn:
        # We need a session to check/add
        pass # Simplified for this demo
    logger.info("Database initialized")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "user-management-service"}

@app.post("/api/auth/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # Check existing
    result = await db.execute(select(models.User).where(models.User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_pw,
        role=user.role
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    logger.info(f"Registered user {user.email}")
    return db_user

@app.post("/api/auth/login", response_model=schemas.Token)
async def login(login_req: schemas.LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email == login_req.email))
    user = result.scalar_one_or_none()
    
    if not user or not auth.verify_password(login_req.password, user.hashed_password):
        # Allow creating the default user on fly if it matches creds (FOR DEMO/TESTING ONLY)
        if login_req.email == "admin@astrazeneca.com" and login_req.password == "admin":
             # Create default admin if it doesn't exist
            if not user:
                hashed_pw = auth.get_password_hash("admin")
                user = models.User(email="admin@astrazeneca.com", hashed_password=hashed_pw, role="ADMIN")
                db.add(user)
                await db.commit()
                await db.refresh(user)
                logger.info("Created default admin user on the fly")
            elif not auth.verify_password("admin", user.hashed_password):
                 raise HTTPException(status_code=401, detail="Invalid credentials")
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role, "userId": user.id},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }

@app.get("/api/users/me", response_model=schemas.UserResponse)
async def read_users_me(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    
    token = authorization.split(" ")[1]
    try:
        # Simple decode without verification of signature across services in this simplified view,
        # but here we are the issuer so we verify.
        payload = auth.jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except auth.jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.get("/api/users", response_model=List[schemas.UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User))
    users = result.scalars().all()
    return users

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(["ADMIN"]))
):
    # Check if user exists
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Prevent deleting the last admin or self (optional, but good for safety)
    # For now, just basic delete
    await db.delete(user)
    await db.commit()
    logger.info(f"Deleted user {user_id}")
    return None
