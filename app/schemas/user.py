from pydantic import BaseModel
from typing import Optional


class UserBase(BaseModel):
    username: str
    full_name: str
    role: str = "member"


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True


class LoginSchema(BaseModel):
    username: str
    password: str
