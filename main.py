from fastapi import FastAPI, Header, HTTPException, Request
import os
import random
import re
import asyncio # We use this for the safe delay

app = FastAPI()

API_KEY = os.getenv("API_KEY", "mysecretkey")

# 1. SMARTER KEYWORDS (Regex ready)
# We look for these words, but we will match them carefully
SCAM_KEYWORDS = [
    "account", "blocked", "verify", "urgent", "upi", "otp", "bank", 
    "suspended", "kyc", "click", "link", "reward", "winner", "update",
    "expire", "alert", "fraud"
]

# 2. CREATIVE "GRANDPA" PERSONA
# Scammers hate wasting time. This persona wastes their time.
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

EXIT_REPLIES = [
    "This is too complicated. I will walk to the bank tomorrow.",
    "My son just walked in, let me ask him.",
    "I am going to the police station to ask about this.",
    "I don't trust this phone anymore. Goodbye."
]

sessions = {}

def safe_success():
    return {"status": "success"}

async def process(request: Request, x_api_key: str | None):
    # --- 1. STABLE VALIDATION (From the working code) ---
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

    # --- 2. SAFE DATA EXTRACTION ---
    session_id = data.get("sessionId", "tester-session")
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

    # --- 3. SMART DETECTION (Whole Word Matching) ---
    # This prevents false alarms (e.g., "cupid" won't trigger "upi")
    scam = False
    for k in SCAM_KEYWORDS:
        # \b looks for word boundaries
        if re.search(r'\b' + re.escape(k) + r'\b', text):
            scam = True
            break

    # --- 4. HUMAN DELAY (Safe) ---
    # We wait 0.1 seconds. Enough to feel real, fast enough for the tester.
    await asyncio.sleep(0.1)

    # --- 5. LOGIC ---
    if scam and count < 3:
        reply = random.choice(CONFUSED_REPLIES)
    elif scam and count < 6:
        reply = random.choice(HELPER_REPLIES)
    elif scam:
        reply = random.choice(EXIT_REPLIES)
    else:
        reply = "Okay."

    # Return exactly what the working code returned (No extra fields)
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
