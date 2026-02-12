from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    role: Optional[str] = "ANALYST"
    is_active: Optional[bool] = Field(default=True, serialization_alias="isActive")

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    created_at: datetime = Field(serialization_alias="createdAt")

    class Config:
        from_attributes = True
