from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Chatbot API")

class Message(BaseModel):
    content: str

class ChatResponse(BaseModel):
    response: str

# In-memory message history (replace with database in later modules)
conversation_history = []

@app.get("/")
def read_root():
    return {"status": "online", "message": "Welcome to the Chatbot API"}

@app.post("/chat", response_model=ChatResponse)
def chat(message: Message):
    # Store message in history
    conversation_history.append(message.content)
    
    # Simple echo response for now
    response = f"You said: {message.content}"
    
    return ChatResponse(response=response)

@app.get("/history")
def get_history():
    return {"history": conversation_history}