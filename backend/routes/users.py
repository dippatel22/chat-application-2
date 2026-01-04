"""
REST API routes for user management.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from models import User, UserCreate, UserLogin, Token
from auth import (
    get_password_hash, 
    authenticate_user, 
    create_access_token,
    get_current_active_user,
    get_user_by_email
)
from database import get_database
from activity import log_activity
from datetime import datetime, timedelta
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    """Register a new user."""
    db = get_database()
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username is taken
    existing_username = await db.users.find_one({"username": user.username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # 🔒 PASSWORD LENGTH CHECK (✅ CORRECT PLACE)
    if len(user.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password too long (maximum 72 characters)"
        )
    
    # Create user
    user_dict = user.model_dump(exclude={"password"})
    user_dict["hashed_password"] = get_password_hash(user.password)
    user_dict["is_active"] = True
    user_dict["is_bot"] = False
    user_dict["created_at"] = datetime.utcnow()
    user_dict["last_seen"] = None
    
    result = await db.users.insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)
    
    # Log activity
    await log_activity(user.email, "User registered", f"New user: {user.username}")
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    created_user = User(**user_dict)
    logger.info(f"New user registered: {user.email}")
    
    return Token(access_token=access_token, user=created_user)


@router.post("/login", response_model=Token)
async def login(user_login: UserLogin):
    """Authenticate user and return token."""
    user = await authenticate_user(user_login.email, user_login.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Log activity
    await log_activity(user.email, "User logged in")
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    user_response = User(
        _id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_bot=user.is_bot,
        created_at=user.created_at,
        last_seen=user.last_seen
    )
    
    logger.info(f"User logged in: {user.email}")
    
    return Token(access_token=access_token, user=user_response)


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


@router.get("/search", response_model=list[User])
async def search_users(
    query: str,
    current_user: User = Depends(get_current_active_user)
):
    """Search users by username or email."""
    db = get_database()
    
    # Search by username or email (partial match)
    users = await db.users.find({
        "$or": [
            {"username": {"$regex": query, "$options": "i"}},
            {"email": {"$regex": query, "$options": "i"}},
            {"full_name": {"$regex": query, "$options": "i"}}
        ],
        "email": {"$ne": current_user.email}  # Exclude current user
    }).limit(20).to_list(20)
    
    # Convert to User models
    user_list = []
    for user_data in users:
        user_data["_id"] = str(user_data["_id"])
        user_list.append(User(**user_data))
    
    return user_list


@router.get("/contacts", response_model=list[User])
async def get_contacts(current_user: User = Depends(get_current_active_user)):
    """Get all users that current user has chatted with."""
    db = get_database()
    
    # Find all unique users that current user has sent or received messages from
    pipeline = [
        {
            "$match": {
                "$or": [
                    {"sender": current_user.email},
                    {"recipient": current_user.email}
                ]
            }
        },
        {
            "$group": {
                "_id": None,
                "contacts": {
                    "$addToSet": {
                        "$cond": [
                            {"$eq": ["$sender", current_user.email]},
                            "$recipient",
                            "$sender"
                        ]
                    }
                }
            }
        }
    ]
    
    result = await db.messages.aggregate(pipeline).to_list(1)
    
    if not result or not result[0].get("contacts"):
        return []
    
    contact_emails = result[0]["contacts"]
    
    # Fetch user details
    users = await db.users.find({"email": {"$in": contact_emails}}).to_list(100)
    
    user_list = []
    for user_data in users:
        user_data["_id"] = str(user_data["_id"])
        user_list.append(User(**user_data))
    
    return user_list







