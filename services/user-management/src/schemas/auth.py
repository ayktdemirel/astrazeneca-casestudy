from pydantic import BaseModel, EmailStr, Field
from .user import UserResponse

class Token(BaseModel):
    access_token: str = Field(serialization_alias="accessToken")
    token_type: str = Field(serialization_alias="tokenType")
    expires_in: int = Field(serialization_alias="expiresIn")
    user: UserResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
