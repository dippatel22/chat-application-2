"""
WebSocket server for real-time messaging using Socket.IO.
"""
import socketio
from typing import Dict, Set
from models import Message
from database import get_database
from activity import log_activity
from bot import ai_bot, AIBot
from datetime import datetime, timezone
from jose import jwt, JWTError
from config import settings
import logging

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=False
)

# Track connected users: {user_email: set(session_ids)}
connected_users: Dict[str, Set[str]] = {}

# Track session to user mapping: {session_id: user_email}
session_users: Dict[str, str] = {}


async def verify_token(token: str) -> str:
    """Verify JWT token and return user email."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise ValueError("Invalid token")
        return email
    except JWTError:
        raise ValueError("Invalid token")


@sio.event
async def connect(sid, environ, auth):
    """Handle client connection."""
    try:
        # Verify authentication
        if not auth or 'token' not in auth:
            logger.warning(f"Connection attempt without token: {sid}")
            return False
        
        token = auth['token']
        user_email = await verify_token(token)
        
        # Store session mapping
        session_users[sid] = user_email
        
        # Add to connected users
        if user_email not in connected_users:
            connected_users[user_email] = set()
        connected_users[user_email].add(sid)
        
        logger.info(f"User connected: {user_email} (session: {sid})")
        
        # Notify user of successful connection
        await sio.emit('connected', {'email': user_email}, room=sid)
        
        # Log activity
        await log_activity(user_email, "WebSocket connected")
        
        return True
        
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return False


@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    try:
        if sid in session_users:
            user_email = session_users[sid]
            
            # Remove from connected users
            if user_email in connected_users:
                connected_users[user_email].discard(sid)
                if not connected_users[user_email]:
                    del connected_users[user_email]
            
            # Remove session mapping
            del session_users[sid]
            
            logger.info(f"User disconnected: {user_email} (session: {sid})")
            
            # Log activity
            await log_activity(user_email, "WebSocket disconnected")
            
    except Exception as e:
        logger.error(f"Disconnection error: {e}")


@sio.event
async def send_message(sid, data):
    """Handle message sending via WebSocket."""
    try:
        # Get sender email
        if sid not in session_users:
            await sio.emit('error', {'message': 'Unauthorized'}, room=sid)
            return
        
        sender_email = session_users[sid]
        
        # Validate message data
        if not data or 'recipient' not in data or 'content' not in data:
            await sio.emit('error', {'message': 'Invalid message data'}, room=sid)
            return
        
        recipient_email = data['recipient']
        content = data['content']
        
        logger.info(f" Message from {sender_email} to {recipient_email}: {content[:50]}")
        logger.info(f" Connected users: {list(connected_users.keys())}")
        logger.info(f" Is recipient online? {recipient_email in connected_users}")
        
        # Create message in database
        db = get_database()
        message_dict = {
            "sender": sender_email,
            "recipient": recipient_email,
            "content": content,
            "is_bot_response": False,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None),
            "status": "Sent"
        }
        
        result = await db.messages.insert_one(message_dict)
        message_dict["_id"] = str(result.inserted_id)
        
        # Create response message
        message_response = {
            "message_id": message_dict["_id"],
            "sender": sender_email,
            "recipient": recipient_email,
            "content": content,
            "timestamp": message_dict["timestamp"].isoformat() + 'Z',
            "status": "Sent",
            "is_bot_response": False
        }
        
        # Send to sender (confirmation)
        await sio.emit('message_sent', message_response, room=sid)
        
        # Send to recipient if online (or if it's the bot)
        if recipient_email in connected_users:
            logger.info(f" Recipient {recipient_email} is ONLINE - sending message")
            # Update message to Delivered status
            message_response_delivered = message_response.copy()
            message_response_delivered["status"] = "Delivered"
            
            logger.info(f" Broadcasting to {len(connected_users[recipient_email])} session(s)")
            for recipient_sid in connected_users[recipient_email]:
                logger.info(f"   → Sending to session {recipient_sid}")
                await sio.emit('new_message', message_response_delivered, room=recipient_sid)
            
            # Update status in database
            await db.messages.update_one(
                {"_id": result.inserted_id},
                {"$set": {"status": "Delivered"}}
            )
            
            # Notify sender about delivery
            delivery_notification = {
                "message_id": message_dict["_id"],
                "status": "Delivered"
            }
            await sio.emit('message_delivered', delivery_notification, room=sid)
        elif recipient_email == AIBot.BOT_EMAIL:
            # Bot always "receives" messages instantly
            await db.messages.update_one(
                {"_id": result.inserted_id},
                {"$set": {"status": "Delivered"}}
            )
            
            # Notify sender that bot received the message
            delivery_notification = {
                "message_id": message_dict["_id"],
                "status": "Delivered"
            }
            await sio.emit('message_delivered', delivery_notification, room=sid)
        else:
            logger.warning(f" Recipient {recipient_email} is OFFLINE - message stored for later")
        
        # Log activity
        await log_activity(sender_email, "Message sent via WebSocket", f"To: {recipient_email}")
        
        # If message is to bot, generate response
        if recipient_email == AIBot.BOT_EMAIL:
            bot_response = ai_bot.process_message(sender_email, content)
            
            # Mark user's message as Read by bot
            await db.messages.update_one(
                {"_id": result.inserted_id},
                {"$set": {"status": "Read"}}
            )
            
            # Notify sender that bot read the message
            read_notification = {
                "message_id": message_dict["_id"],
                "status": "Read"
            }
            await sio.emit('message_read', read_notification, room=sid)
            
            # Create bot message in database
            bot_message_dict = {
                "sender": AIBot.BOT_EMAIL,
                "recipient": sender_email,
                "content": bot_response,
                "is_bot_response": True,
                "timestamp": datetime.now(timezone.utc).replace(tzinfo=None),
                "status": "Sent"
            }
            
            bot_result = await db.messages.insert_one(bot_message_dict)
            bot_message_dict["_id"] = str(bot_result.inserted_id)
            
            # Send bot response
            bot_response_message = {
                "message_id": bot_message_dict["_id"],
                "sender": AIBot.BOT_EMAIL,
                "recipient": sender_email,
                "content": bot_response,
                "timestamp": bot_message_dict["timestamp"].isoformat() + 'Z',
                "status": "Delivered",
                "is_bot_response": True
            }
            
            # Send to all user's sessions
            if sender_email in connected_users:
                for user_sid in connected_users[sender_email]:
                    await sio.emit('new_message', bot_response_message, room=user_sid)
                
                # Mark bot message as delivered and read immediately
                await db.messages.update_one(
                    {"_id": bot_result.inserted_id},
                    {"$set": {"status": "Read"}}
                )
            
            # Log bot activity
            await log_activity(AIBot.BOT_EMAIL, "Bot replied via WebSocket", f"To: {sender_email}")
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        await sio.emit('error', {'message': 'Failed to send message'}, room=sid)


@sio.event
async def mark_as_read(sid, data):
    """Mark message as read."""
    try:
        if sid not in session_users:
            return
        
        user_email = session_users[sid]
        
        if not data or 'message_id' not in data:
            return
        
        message_id = data['message_id']
        
        # Update message status
        db = get_database()
        from bson import ObjectId
        
        if not ObjectId.is_valid(message_id):
            return
        
        result = await db.messages.update_one(
            {
                "_id": ObjectId(message_id),
                "recipient": user_email
            },
            {"$set": {"status": "Read"}}
        )
        
        if result.modified_count > 0:
            # Get message to notify sender
            message = await db.messages.find_one({"_id": ObjectId(message_id)})
            if message:
                sender_email = message['sender']
                
                # Notify sender if online
                if sender_email in connected_users:
                    read_notification = {
                        "message_id": message_id,
                        "status": "Read",
                        "read_by": user_email
                    }
                    for sender_sid in connected_users[sender_email]:
                        await sio.emit('message_read', read_notification, room=sender_sid)
            
            # Log activity
            await log_activity(user_email, "Message marked as read", f"Message ID: {message_id}")
        
    except Exception as e:
        logger.error(f"Error marking message as read: {e}")


@sio.event
async def typing(sid, data):
    """Handle typing indicator."""
    try:
        if sid not in session_users:
            return
        
        sender_email = session_users[sid]
        
        if not data or 'recipient' not in data:
            return
        
        recipient_email = data['recipient']
        is_typing = data.get('is_typing', True)
        
        # Send typing indicator to recipient if online
        if recipient_email in connected_users:
            typing_data = {
                "sender": sender_email,
                "is_typing": is_typing
            }
            for recipient_sid in connected_users[recipient_email]:
                await sio.emit('user_typing', typing_data, room=recipient_sid)
        
    except Exception as e:
        logger.error(f"Error handling typing indicator: {e}")


@sio.event
async def get_online_status(sid, data):
    """Check if a user is online."""
    try:
        if not data or 'email' not in data:
            return
        
        email = data['email']
        is_online = email in connected_users
        
        await sio.emit('online_status', {
            'email': email,
            'is_online': is_online
        }, room=sid)
        
    except Exception as e:
        logger.error(f"Error checking online status: {e}")


def get_socketio_app():
    """Get Socket.IO ASGI application."""
    return socketio.ASGIApp(sio)

