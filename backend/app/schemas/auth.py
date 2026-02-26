from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    agency_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    agency_id: str
    user_id: str


class ApiKeyResponse(BaseModel):
    api_key: str
    message: str = "Store this key securely — it cannot be retrieved again."
