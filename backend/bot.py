"""
AI Bot with intent-response framework for WhatsApp-like interactions.
"""
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Intent:
    """Represents a bot intent with patterns and responses."""
    
    def __init__(self, name: str, patterns: List[str], responses: List[str], context_required: bool = False):
        self.name = name
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        self.responses = responses
        self.context_required = context_required
    
    def match(self, text: str) -> bool:
        """Check if text matches any pattern."""
        return any(pattern.search(text) for pattern in self.patterns)


class BotContext:
    """Maintains conversation context for a user."""
    
    def __init__(self):
        self.history: List[Dict] = []
        self.last_intent: Optional[str] = None
        self.user_data: Dict = {}
    
    def add_message(self, message: str, is_user: bool, intent: Optional[str] = None):
        """Add a message to conversation history."""
        self.history.append({
            "message": message,
            "is_user": is_user,
            "intent": intent,
            "timestamp": datetime.utcnow()
        })
        if intent:
            self.last_intent = intent
    
    def get_recent_messages(self, count: int = 5) -> List[Dict]:
        """Get recent messages from history."""
        return self.history[-count:]


class AIBot:
    """AI Bot with intent-based response system."""
    
    BOT_EMAIL = "whatsease@bot.com"
    BOT_NAME = "WhatsEase"
    
    def __init__(self):
        self.intents = self._initialize_intents()
        self.user_contexts: Dict[str, BotContext] = {}
        logger.info("AI Bot initialized")
    
    def _initialize_intents(self) -> List[Intent]:
        """Initialize bot intents with patterns and responses."""
        return [
            Intent(
                "greeting",
                [r"\b(hi|hello|hey|greetings|good morning|good evening|good afternoon)\b"],
                [
                    "Hello! I'm WhatsEase, your AI assistant. How can I help you today?",
                    "Hi there! I'm WhatsEase. What can I do for you?",
                    "Hey! WhatsEase here. How may I assist you?"
                ]
            ),
            Intent(
                "goodbye",
                [r"\b(bye|goodbye|see you|talk later|take care)\b"],
                [
                    "Goodbye! Feel free to reach out anytime!",
                    "See you later! Have a great day!",
                    "Take care! I'm always here if you need assistance."
                ]
            ),
            Intent(
                "help",
                [r"\b(help|assist|support|what can you do)\b"],
                [
                    "I'm WhatsEase, your AI assistant! I can help you with:\n"
                    "• General questions and conversation\n"
                    "• Information about weather and time\n"
                    "• Setting reminders\n"
                    "• Quick calculations\n"
                    "Just ask me anything!"
                ]
            ),
            Intent(
                "weather",
                [r"\b(weather|temperature|forecast|climate)\b"],
                [
                    "I can help with weather information! For the most accurate data, "
                    "I'd need to integrate with a weather API. Where would you like to check the weather?",
                    "Weather queries are one of my specialties! Which location are you interested in?"
                ]
            ),
            Intent(
                "time",
                [r"\b(time|what time|current time|clock)\b"],
                [
                    f"The current time is {datetime.utcnow().strftime('%H:%M:%S')} UTC. "
                    "Would you like the time in a specific timezone?"
                ]
            ),
            Intent(
                "reminder",
                [r"\b(remind|reminder|remember|don't forget)\b"],
                [
                    "I can help set reminders! Please tell me what you'd like to be reminded about "
                    "and when.",
                    "Reminder feature coming up! What should I remind you about?"
                ]
            ),
            Intent(
                "math",
                [r"\b(calculate|compute|math|add|subtract|multiply|divide|\+|\-|\*|\/)\b"],
                [
                    "I can help with calculations! What would you like me to compute?",
                    "Math is my strong suit! Give me an expression to calculate."
                ]
            ),
            Intent(
                "name_query",
                [r"\b(your name|who are you|what are you)\b"],
                [
                    "I'm WhatsEase, an AI-powered assistant designed to help you with various tasks!",
                    "My name is WhatsEase. I'm here to make your life easier through intelligent assistance."
                ]
            ),
            Intent(
                "thanks",
                [r"\b(thanks|thank you|appreciate|grateful)\b"],
                [
                    "You're welcome! Happy to help!",
                    "My pleasure! Let me know if you need anything else.",
                    "Glad I could help! Feel free to ask anytime."
                ]
            ),
            Intent(
                "how_are_you",
                [r"\b(how are you|how's it going|how do you do)\b"],
                [
                    "I'm functioning perfectly, thank you for asking! How can I assist you today?",
                    "I'm doing great! Ready to help you with whatever you need.",
                    "All systems operational! What can I do for you?"
                ]
            ),
            Intent(
                "joke",
                [r"\b(joke|funny|make me laugh|humor)\b"],
                [
                    "Why don't programmers like nature? It has too many bugs! 🐛",
                    "What's a programmer's favorite hangout place? Foo Bar! 🍺",
                    "Why do Java developers wear glasses? Because they don't C#! 👓"
                ]
            ),
            Intent(
                "fallback",
                [r".*"],
                [
                    "I'm not sure I understand. Could you rephrase that?",
                    "Interesting! Can you tell me more about what you need?",
                    "I'm still learning! Could you ask that in a different way?",
                    "That's a bit outside my current knowledge. Try asking me about weather, time, or general help!"
                ]
            )
        ]
    
    def _get_context(self, user_email: str) -> BotContext:
        """Get or create context for a user."""
        if user_email not in self.user_contexts:
            self.user_contexts[user_email] = BotContext()
        return self.user_contexts[user_email]
    
    def _match_intent(self, message: str) -> Intent:
        """Match message to an intent."""
        for intent in self.intents:
            if intent.name != "fallback" and intent.match(message):
                return intent
        
        # Return fallback if no match
        return self.intents[-1]
    
    def _calculate_expression(self, message: str) -> Optional[str]:
        """Attempt to calculate a mathematical expression."""
        try:
            # Extract numbers and operators
            expression = re.search(r'[\d\+\-\*/\(\)\.\s]+', message)
            if expression:
                expr_str = expression.group().strip()
                # Safe evaluation
                result = eval(expr_str, {"__builtins__": {}}, {})
                return f"The answer is: {result}"
        except Exception as e:
            logger.debug(f"Failed to calculate expression: {e}")
        return None
    
    def process_message(self, user_email: str, message: str) -> str:
        """Process user message and generate bot response."""
        context = self._get_context(user_email)
        
        # Add user message to context
        matched_intent = self._match_intent(message)
        context.add_message(message, is_user=True, intent=matched_intent.name)
        
        # Special handling for math intent
        if matched_intent.name == "math":
            calc_result = self._calculate_expression(message)
            if calc_result:
                response = calc_result
            else:
                response = matched_intent.responses[0]
        else:
            # Get response based on context
            import random
            response = random.choice(matched_intent.responses)
        
        # Add bot response to context
        context.add_message(response, is_user=False, intent=matched_intent.name)
        
        logger.info(f"Bot processed message from {user_email} - Intent: {matched_intent.name}")
        return response
    
    def get_conversation_history(self, user_email: str, count: int = 10) -> List[Dict]:
        """Get conversation history for a user."""
        context = self._get_context(user_email)
        return context.get_recent_messages(count)
    
    def clear_context(self, user_email: str):
        """Clear conversation context for a user."""
        if user_email in self.user_contexts:
            del self.user_contexts[user_email]
            logger.info(f"Cleared context for {user_email}")


# Global bot instance
ai_bot = AIBot()







