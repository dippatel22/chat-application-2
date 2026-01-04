"""
REST API routes for message management.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from models import Message, MessageCreate, MessageUpdate, User, ChatListItem
from auth import get_current_active_user
from database import get_database
from activity import log_activity
from bot import ai_bot, AIBot
from datetime import datetime, timezone
from bson import ObjectId
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.post("/", response_model=Message, status_code=status.HTTP_201_CREATED)
async def create_message(
    message: MessageCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new message."""
    # Verify sender is current user
    if message.sender != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot send message as another user"
        )
    
    db = get_database()
    
    # Check if recipient exists (unless it's the bot)
    if message.recipient != AIBot.BOT_EMAIL:
        recipient = await db.users.find_one({"email": message.recipient})
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipient not found"
            )
    
    # Create message
    message_dict = message.model_dump()
    message_dict["timestamp"] = datetime.now(timezone.utc).replace(tzinfo=None)
    message_dict["status"] = "Sent"
    
    result = await db.messages.insert_one(message_dict)
    message_dict["_id"] = str(result.inserted_id)
    
    # Log activity
    await log_activity(
        current_user.email,
        "Message sent",
        f"To: {message.recipient}"
    )
    
    created_message = Message(**message_dict)
    logger.info(f"Message created: {current_user.email} -> {message.recipient}")
    
    # If message is to bot, generate response
    if message.recipient == AIBot.BOT_EMAIL:
        bot_response = ai_bot.process_message(current_user.email, message.content)
        
        # Create bot response message
        bot_message_dict = {
            "sender": AIBot.BOT_EMAIL,
            "recipient": current_user.email,
            "content": bot_response,
            "is_bot_response": True,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None),
            "status": "Sent"
        }
        
        await db.messages.insert_one(bot_message_dict)
        
        # Log bot activity
        await log_activity(
            AIBot.BOT_EMAIL,
            "Bot replied",
            f"To: {current_user.email}"
        )
    
    return created_message


@router.get("/", response_model=List[Message])
async def get_messages(
    contact_email: str,
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user)
):
    """Get messages between current user and a contact."""
    db = get_database()
    
    logger.info(f"Getting messages between {current_user.email} and {contact_email}, limit={limit}, skip={skip}")
    
    # Find messages between current user and contact
    messages = await db.messages.find({
        "$or": [
            {"sender": current_user.email, "recipient": contact_email},
            {"sender": contact_email, "recipient": current_user.email}
        ]
    }).sort("timestamp", 1).skip(skip).limit(limit).to_list(limit)
    
    logger.info(f"Found {len(messages)} messages")
    
    # Convert to Message models
    message_list = []
    for msg in messages:
        msg["_id"] = str(msg["_id"])
        message_list.append(Message(**msg))
    
    # Mark unread messages as delivered
    await db.messages.update_many(
        {
            "sender": contact_email,
            "recipient": current_user.email,
            "status": "Sent"
        },
        {"$set": {"status": "Delivered"}}
    )
    
    logger.info(f"Returning {len(message_list)} messages to client")
    return message_list


@router.patch("/{message_id}", response_model=Message)
async def update_message(
    message_id: str,
    message_update: MessageUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update message status (e.g., mark as read)."""
    db = get_database()
    
    # Validate ObjectId
    if not ObjectId.is_valid(message_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID"
        )
    
    # Find message
    message = await db.messages.find_one({"_id": ObjectId(message_id)})
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Verify user is recipient (only recipient can update status)
    if message["recipient"] != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recipient can update message status"
        )
    
    # Update message
    update_data = message_update.model_dump(exclude_unset=True)
    if update_data:
        await db.messages.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": update_data}
        )
    
    # Get updated message
    updated_message = await db.messages.find_one({"_id": ObjectId(message_id)})
    updated_message["_id"] = str(updated_message["_id"])
    
    # Log activity
    if message_update.status:
        await log_activity(
            current_user.email,
            f"Message marked as {message_update.status}",
            f"Message ID: {message_id}"
        )
    
    return Message(**updated_message)


@router.get("/chats", response_model=List[ChatListItem])
async def get_chat_list(current_user: User = Depends(get_current_active_user)):
    """Get list of all chats for current user."""
    db = get_database()
    
    # Aggregate pipeline to get chat list with last message
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
            "$sort": {"timestamp": -1}
        },
        {
            "$group": {
                "_id": {
                    "$cond": [
                        {"$eq": ["$sender", current_user.email]},
                        "$recipient",
                        "$sender"
                    ]
                },
                "last_message": {"$first": "$content"},
                "last_message_time": {"$first": "$timestamp"},
                "messages": {"$push": "$$ROOT"}
            }
        },
        {
            "$sort": {"last_message_time": -1}
        }
    ]
    
    chats = await db.messages.aggregate(pipeline).to_list(100)
    
    # Get user details and unread counts
    chat_list = []
    for chat in chats:
        contact_email = chat["_id"]
        
        # Get contact details
        contact = await db.users.find_one({"email": contact_email})
        if not contact:
            continue
        
        # Count unread messages
        unread_count = await db.messages.count_documents({
            "sender": contact_email,
            "recipient": current_user.email,
            "status": {"$ne": "Read"}
        })
        
        chat_item = ChatListItem(
            contact_email=contact_email,
            contact_name=contact.get("username", contact_email),
            last_message=chat["last_message"],
            last_message_time=chat["last_message_time"],
            unread_count=unread_count,
            is_bot=contact.get("is_bot", False)
        )
        chat_list.append(chat_item)
    
    return chat_list


@router.get("/search", response_model=List[Message])
async def search_messages(
    query: str,
    contact_email: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Search messages by content."""
    db = get_database()
    
    # Build search filter
    search_filter = {
        "$or": [
            {"sender": current_user.email},
            {"recipient": current_user.email}
        ],
        "content": {"$regex": query, "$options": "i"}
    }
    
    # Add contact filter if specified
    if contact_email:
        search_filter["$or"] = [
            {"sender": current_user.email, "recipient": contact_email},
            {"sender": contact_email, "recipient": current_user.email}
        ]
    
    messages = await db.messages.find(search_filter).sort("timestamp", -1).limit(50).to_list(50)
    
    # Convert to Message models
    message_list = []
    for msg in messages:
        msg["_id"] = str(msg["_id"])
        message_list.append(Message(**msg))
    
    return message_list


