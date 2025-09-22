from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional
import re

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least 1 uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least 1 lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least 1 number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least 1 special character')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Password reset schemas
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    password: str = Field(..., min_length=8)
    confirm_password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least 1 uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least 1 lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least 1 number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least 1 special character')
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class NoteBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)

class NoteCreate(NoteBase):
    pass

class NoteUpdate(NoteBase):
    pass

class NoteOut(NoteBase):
    id: int
    created_at: datetime
    updated_at: datetime
    owner_id: int

    class Config:
        orm_mode = True