from fastapi import FastAPI, Header, HTTPException, Request
import os
import random

app = FastAPI()

API_KEY = os.getenv("API_KEY", "mysecretkey")

# 1. SMARTER KEYWORDS
# We added spaces around words like " upi " so "cupid" doesn't trigger it.
SCAM_KEYWORDS = [
    "account", "blocked", "verify", "urgent", " upi ", " otp ", "bank", 
    "suspended", "click", "link", "reward", "winner"
]

# 2. THE GRANDPA PERSONA (Creative Replies)
CONFUSED_REPLIES = [
    "Hello? My grandson usually handles the computer.",
    "I received a message about my bank. Is this the manager?",
    "I don't have my glasses, what does this say?",
    "Why is the bank texting me at this hour?",
    "Is my money safe? I am very worried."
]

HELPER_REPLIES = [
    "Okay, I want to fix this. Which specific account is it?",
    "My son told me never to share the OTP, but I am scared.",
    "Do I need to come to the branch? Or can I do it here?",
    "I am trying to find the app. Which one do I download?",
    "Can you send the link again? My fingers are shaky."
]

sessions = {}

def safe_success():
    return {"status": "success"}

async def process(request: Request, x_api_key: str | None):
    # --- SAFETY CHECK: Same as the working code ---
    if x_api_key and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    try:
        body_bytes = await request.body()
        if not body_bytes:
            data = {}
        else:
            data = await request.json()
            if not isinstance(data, dict):
                data = {}
    except Exception:
        data = {}

    session_id = data.get("sessionId", "tester-session")
    
    # Handle message safely
    raw_message = data.get("message", {})
    text = ""
    if isinstance(raw_message, dict):
        text = str(raw_message.get("text", "")).lower()
    else:
        text = str(raw_message).lower()

    if session_id not in sessions:
        sessions[session_id] = {"count": 0}

    sessions[session_id]["count"] += 1
    count = sessions[session_id]["count"]

    # Simple logic
    scam = any(k in text for k in SCAM_KEYWORDS)

    if scam and count < 3:
        reply = random.choice(CONFUSED_REPLIES)
    elif scam:
        reply = random.choice(HELPER_REPLIES)
    else:
        reply = "Okay."

    return {
        "status": "success",
        "scamDetected": scam,
        "messageCount": count,
        "reply": reply
    }

# GET HANDLERS
@app.get("/")
async def root_get():
    return safe_success()

@app.get("/honeypot")
async def honeypot_get():
    return safe_success()

# POST HANDLERS
@app.post("/")
async def root_post(request: Request, x_api_key: str | None = Header(None)):
    return await process(request, x_api_key)

@app.post("/honeypot")
async def honeypot_post(request: Request, x_api_key: str | None = Header(None)):
    return await process(request, x_api_key)
