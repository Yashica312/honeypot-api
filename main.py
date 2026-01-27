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

# 🧠 Memory store (in-memory)
sessions = {}

@app.post("/honeypot")
async def honeypot_endpoint(
    data: dict,
    x_api_key: str = Header(None)
):
    # 1. API key check
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # 2. Get sessionId
    session_id = data.get("sessionId", "unknown-session")

    # 3. Initialize session memory if new
    if session_id not in sessions:
        sessions[session_id] = {
            "message_count": 0,
            "start_time": time.time()
        }

    # 4. Update memory
    sessions[session_id]["message_count"] += 1
    message_count = sessions[session_id]["message_count"]

    # 5. Read message text safely
    message = data.get("message", {})
    text = message.get("text", "")
    text_lower = text.lower()

    # 6. Scam detection
    scam_detected = any(word in text_lower for word in SCAM_KEYWORDS)

    # 7. Simple memory-aware reply
    if scam_detected:
        if message_count < 3:
            reply = "I’m not sure what this means, can you explain?"
        else:
            reply = "I’m still confused. Why is this happening?"
    else:
        reply = "Okay."

    # 8. Response
    return {
        "status": "success",
        "scamDetected": scam_detected,
        "messageCount": message_count,
        "reply": reply
    }
