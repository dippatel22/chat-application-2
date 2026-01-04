"""
Activity logging utilities.
"""
from database import get_database
from models import ActivityLog
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def log_activity(user_email: str, action: str, details: str = None):
    """Log user activity to database."""
    try:
        db = get_database()
        activity = {
            "user_email": user_email,
            "action": action,
            "details": details,
            "timestamp": datetime.utcnow()
        }
        await db.activity_logs.insert_one(activity)
        logger.info(f"Activity logged: {user_email} - {action}")
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")


async def get_recent_activities(limit: int = 50):
    """Get recent activity logs."""
    try:
        db = get_database()
        activities = await db.activity_logs.find().sort("timestamp", -1).limit(limit).to_list(limit)
        
        # Convert ObjectId to string
        for activity in activities:
            activity["_id"] = str(activity["_id"])
        
        return activities
    except Exception as e:
        logger.error(f"Failed to retrieve activities: {e}")
        return []


async def get_user_activities(user_email: str, limit: int = 20):
    """Get activity logs for a specific user."""
    try:
        db = get_database()
        activities = await db.activity_logs.find(
            {"user_email": user_email}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        # Convert ObjectId to string
        for activity in activities:
            activity["_id"] = str(activity["_id"])
        
        return activities
    except Exception as e:
        logger.error(f"Failed to retrieve user activities: {e}")
        return []





