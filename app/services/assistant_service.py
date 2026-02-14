import logging
import re
from typing import Dict, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    user_id: int
    message: str
    user_name: Optional[str] = None
    context: Optional[Dict] = {}

class ChatResponse(BaseModel):
    response: str
    suggestions: List[str] = []

class AssistantService:
    """
    AI Assistant Service for CivicFix
    
    Currently uses rule-based intent matching. 
    Ready to be upgraded to use LLMs (Transformer/OpenAI) in the future.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define intents and responses
        self.intents = {
            'greeting': {
                'patterns': [r'\bhi\b', r'\bhello\b', r'\bhey\b', r'\bstart\b'],
                'response': "Hello! I'm your CivicFix assistant. I can help you report issues, track their status, or explain how the platform works. What would you like to do?",
                'suggestions': ["Report an issue", "Check issue status", "How it works"]
            },
            'report_issue': {
                'patterns': [r'\breport\b', r'\bnew issue\b', r'\bcreate\b', r'\bsubmit\b'],
                'response': "To report an issue, tap the '+' button at the bottom of the screen. You'll need to take a photo, select a category, and confirm the location. Should I give you some tips on taking good photos?",
                'suggestions': ["Photo tips", "Categories", "Start reporting"]
            },
            'status': {
                'patterns': [r'\bstatus\b', r'\btrack\b', r'\bcheck\b', r'\bupdate\b'],
                'response': "You can check the status of your reports in the 'My Issues' tab. Issues go through AI verification first, then are assigned to government officials. Have you submitted an issue recently?",
                'suggestions': ["My Issues", "Explain verification", "Escalation"]
            },
            'escalation': {
                'patterns': [r'\bescalat', r'\bdelay\b', r'\bslow\b', r'\bwaiting\b', r'\blong time\b'],
                'response': "If an issue remains unresolved for more than 30 days, our system automatically escalates it to higher authorities. You'll receive a notification when this happens. You can also manually trigger an escalation if you verify that a 'resolved' issue is actually not fixed.",
                'suggestions': ["Check escalation status", "Verify resolution"]
            },
            'verification': {
                'patterns': [r'\bverify\b', r'\bverification\b', r'\bai check\b'],
                'response': "We use AI to verify all reports. We check for fake images, duplicates, and location consistency. This ensures that authorities trust the data we send them.",
                'suggestions': ["Why was I rejected?", "Report issue"]
            },
            'trust_score': {
                'patterns': [r'\btrust\b', r'\bscore\b', r'\bpoints\b'],
                'response': "Your Trust Score reflects the quality of your reports. It goes up when issues are verified and fixed, and down if reports are rejected as fake. High trust scores may give your future reports higher priority.",
                'suggestions': ["Check my score", "Improve score"]
            }
        }
        
        # Default fallback
        self.fallback = {
            'response': "I'm not sure I understood that. I can help with reporting issues, checking status, or explaining the platform.",
            'suggestions': ["Report an issue", "How it works", "Contact support"]
        }

    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process a user message and return a response"""
        try:
            message = request.message.lower().strip()
            
            # Simple keyword matching
            matched_intent = None
            
            for intent_name, data in self.intents.items():
                for pattern in data['patterns']:
                    if re.search(pattern, message):
                        matched_intent = data
                        break
                if matched_intent:
                    break
            
            if matched_intent:
                response = matched_intent['response']
                suggestions = matched_intent['suggestions']
                
                # Personalize if possible
                if request.user_name and intent_name == 'greeting':
                    response = f"Hello {request.user_name}! " + response.split('! ', 1)[1]
                    
                return ChatResponse(response=response, suggestions=suggestions)
            
            return ChatResponse(
                response=self.fallback['response'],
                suggestions=self.fallback['suggestions']
            )
            
        except Exception as e:
            self.logger.error(f"Error processing chat: {e}")
            return ChatResponse(
                response="I'm having a bit of trouble right now. Please try again.",
                suggestions=[]
            )
