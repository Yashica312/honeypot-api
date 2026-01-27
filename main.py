from fastapi import FastAPI, Header, HTTPException
import os
import time

app = FastAPI()

API_KEY = os.getenv("API_KEY", "mysecretkey")

SCAM_KEYWORDS = [
    "account blocked",
    "verify",
    "urgent",
    "upi",
    "otp",
    "bank",
    "suspended"
]

# In-memory session store
sessions = {}

@app.post("/honeypot")
async def honeypot_endpoint(
    data: dict,
    x_api_key: str = Header(None)
):
    # API key check
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    session_id = data.get("sessionId", "unknown-session")

    # Initialize session if new
    if session_id not in sessions:
        sessions[session_id] = {
            "message_count": 0,
            "start_time": time.time()
        }

    # Update message count
    sessions[session_id]["message_count"] += 1
    message_count = sessions[session_id]["message_count"]

    # Read message text
    message = data.get("message", {})
    text = message.get("text", "")
    text_lower = text.lower()

    # Scam detection
    scam_detected = any(word in text_lower for word in SCAM_KEYWORDS)

    # PERSONA SWITCHING LOGIC
    if scam_detected:
        if message_count < 3:
            # Persona A: Confused User
            reply = "I don’t really understand this. Can you explain it clearly?"
        else:
            # Persona B: Concerned Helper
            reply = "I’m helping them with this. Which bank is this from exactly?"
    else:
        reply = "Okay."

    return {
        "status": "success",
        "scamDetected": scam_detected,
        "messageCount": message_count,
        "reply": reply
    }
