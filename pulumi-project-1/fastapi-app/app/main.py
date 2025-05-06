from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import random

app = FastAPI(title="Chatbot API")

# Simple in-memory storage for chat messages
chat_history: Dict[str, List[Dict[str, str]]] = {}

class Message(BaseModel):
    content: str
    role: str = "user"  # "user" or "bot"

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    session_id: str

# Simple responses the bot can give
BOT_RESPONSES = [
    "That's interesting! Tell me more.",
    "I understand. How does that make you feel?",
    "Can you elaborate on that?",
    "I see. What happened next?",
    "Thanks for sharing that with me.",
    "I'm here to help. What else is on your mind?",
]

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "chatbot-api"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Generate a new session ID if none provided
    session_id = request.session_id or f"session_{random.randint(1000, 9999)}"
    
    # Initialize chat history for new sessions
    if session_id not in chat_history:
        chat_history[session_id] = []
    
    # Store user message
    chat_history[session_id].append({
        "content": request.message,
        "role": "user"
    })
    
    # Generate a simple response
    bot_reply = random.choice(BOT_RESPONSES)
    
    # Store bot response
    chat_history[session_id].append({
        "content": bot_reply,
        "role": "bot"
    })
    
    return ChatResponse(reply=bot_reply, session_id=session_id)


@app.get("/history/{session_id}", response_model=List[Message])
def get_chat_history(session_id: str):
    if session_id not in chat_history:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return [Message(content=msg["content"], role=msg["role"]) 
            for msg in chat_history[session_id]]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)