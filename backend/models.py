"""
Data models for the chat application.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom type for MongoDB ObjectId."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation model."""
    password: str


class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr
    password: str


class User(UserBase):
    """User model with database fields."""
    id: str = Field(alias="_id")
    is_active: bool = True
    is_bot: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class UserInDB(User):
    """User model with hashed password."""
    hashed_password: str


class Token(BaseModel):
    """JWT token response model."""
    access_token: str
    token_type: str = "bearer"
    user: User


class MessageStatus(str):
    """Message status enumeration."""
    SENT = "Sent"
    DELIVERED = "Delivered"
    READ = "Read"


class MessageBase(BaseModel):
    """Base message model."""
    sender: EmailStr
    recipient: EmailStr
    content: str
    is_bot_response: bool = False


class MessageCreate(MessageBase):
    """Message creation model."""
    pass


class Message(MessageBase):
    """Message model with database fields."""
    message_id: str = Field(alias="_id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["Sent", "Delivered", "Read"] = "Sent"
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat() + 'Z' if v else None  # Force UTC with Z suffix
        }


class MessageUpdate(BaseModel):
    """Message update model."""
    status: Optional[Literal["Sent", "Delivered", "Read"]] = None


class ActivityLog(BaseModel):
    """Activity log model."""
    id: Optional[str] = Field(alias="_id", default=None)
    user_email: EmailStr
    action: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class ChatListItem(BaseModel):
    """Chat list item for UI."""
    contact_email: EmailStr
    contact_name: str
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int = 0
    is_bot: bool = False


