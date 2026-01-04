"""
REST API routes for activity logs and bot interaction.
"""
from fastapi import APIRouter, Depends, Query
from models import User, ActivityLog
from auth import get_current_active_user
from activity import get_recent_activities, get_user_activities
from bot import ai_bot
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["activity"])


@router.get("/activities", response_model=List[ActivityLog])
async def get_activities(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user)
):
    """Get recent activity logs."""
    activities = await get_recent_activities(limit)
    return [ActivityLog(**activity) for activity in activities]


@router.get("/activities/me", response_model=List[ActivityLog])
async def get_my_activities(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """Get activity logs for current user."""
    activities = await get_user_activities(current_user.email, limit)
    return [ActivityLog(**activity) for activity in activities]


@router.get("/bot/history")
async def get_bot_conversation_history(
    count: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user)
):
    """Get conversation history with bot."""
    history = ai_bot.get_conversation_history(current_user.email, count)
    return {"history": history}


@router.delete("/bot/history")
async def clear_bot_conversation_history(
    current_user: User = Depends(get_current_active_user)
):
    """Clear conversation history with bot."""
    ai_bot.clear_context(current_user.email)
    return {"message": "Conversation history cleared"}





