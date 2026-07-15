from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    professional_id: str
    name: str
    token: str


class User(BaseModel):
    username: str
    password: str
    professional_id: str
