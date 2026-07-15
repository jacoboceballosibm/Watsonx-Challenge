from pydantic import BaseModel
from enum import Enum


class UserRole(str, Enum):
    CANDIDATE = "candidate"
    OWNER = "owner"
    ADMIN = "admin"


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    professional_id: str
    user_id: str
    name: str
    token: str
    role: UserRole


class User(BaseModel):
    username: str
    password: str
    professional_id: str
    user_id: str
    role: UserRole = UserRole.CANDIDATE
