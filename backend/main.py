"""
Main FastAPI application with Socket.IO integration.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys
import socketio


from config import settings
from database import connect_to_mongo, close_mongo_connection, create_indexes, get_database
from routes import users, messages, activity
from socket_manager import sio, get_socketio_app
from bot import AIBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting application...")
    await connect_to_mongo()
    await create_indexes()
    await initialize_bot_user()
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await close_mongo_connection()
    logger.info("Application shutdown complete")


async def initialize_bot_user():
    """Initialize bot user in database."""
    db = get_database()
    
    bot_email = AIBot.BOT_EMAIL
    bot = await db.users.find_one({"email": bot_email})
    
    if not bot:
        from auth import get_password_hash
        from datetime import datetime
        
        bot_user = {
            "email": bot_email,
            "username": AIBot.BOT_NAME,
            "full_name": "WhatsEase AI Assistant",
            "hashed_password": get_password_hash("bot_password_not_used"),
            "is_active": True,
            "is_bot": True,
            "created_at": datetime.utcnow(),
            "last_seen": None
        }
        
        await db.users.insert_one(bot_user)
        logger.info("Bot user initialized")


# Create FastAPI application
app = FastAPI(
    title="WhatsApp-like Chat Application",
    description="Real-time chat application with AI bot integration",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(messages.router)
app.include_router(activity.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "WhatsApp-like Chat Application API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Mount Socket.IO app
socket_app = get_socketio_app()
app.mount("/socket.io", socket_app)

# For direct Socket.IO access (without FastAPI routing)
combined_app = socketio.ASGIApp(sio, app)





