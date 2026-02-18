from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    store_id: int | None
    full_name: str | None


class TokenData(BaseModel):
    user_id: int
    role: str
    store_id: int | None
