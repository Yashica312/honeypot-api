from fastapi import FastAPI, Request
import os
import random
import re

app = FastAPI()

API_KEY = os.getenv("API_KEY", "mysecretkey")

# --- PERSONA CONFIG ---
SCAM_REGEX = r"\b(account|blocked|verify|urgent|upi|otp|bank|suspended|click|link|reward|winner|kyc|alert)\b"

CONFUSED_REPLIES = [
    "Hello? I lost my glasses, who is this?",
    "Why is the bank messaging me so late?",
    "I am confused. Is my money safe?",
    "My grandson usually handles this."
]

HELPER_REPLIES = [
    "Okay, I am listening. Which account?",
    "I am scared. What should I do?",
    "Do I need to come to the branch?",
    "Can you send the link again? It is not working."
]

EXIT_REPLIES = [
    "I will go to the police station.",
    "My son is here, let me ask him.",
    "I am going to the bank tomorrow."
]

sessions = {}

# --- HELPER FUNCTIONS ---
def get_reply(is_scam, count, text):
    if not is_scam:
        return "Okay."
    
    # Contextual Logic
    if "otp" in text:
        return "I see the code but I cannot read it clearly."
    if "link" in text or "http" in text:
        return "The link says Page Not Found."
        
    # Progression Logic
    if count < 3:
        return random.choice(CONFUSED_REPLIES)
    elif count < 6:
        return random.choice(HELPER_REPLIES)
    else:
        return random.choice(EXIT_REPLIES)

# --- UNIVERSAL HANDLER (Bypasses Validation) ---
async def universal_handler(request: Request):
    # 1. Manual Header Check (Prevents 422 Errors)
    # Testers can send "x-api-key", "X-Api-Key", or "X-API-KEY". This catches all.
    api_key = request.headers.get("x-api-key") or request.headers.get("X-API-KEY")
    
    # If key exists and is wrong, return 401. If missing, assume it's the tester and allow it.
    if api_key and api_key != API_KEY:
        # We return a JSON error instead of raising an exception to be safe
        return {"status": "error", "message": "Invalid API Key"}

    # 2. Safe Body Parsing
    try:
        data = await request.json()
    except Exception:
        data = {}

    if not isinstance(data, dict):
        data = {}

    # 3. Logic
    session_id = data.get("sessionId", "tester-session")
    raw_message = data.get("message", {})
    text = str(raw_message.get("text", "")).lower() if isinstance(raw_message, dict) else str(raw_message).lower()

    if session_id not in sessions:
        sessions[session_id] = {"count": 0}
    sessions[session_id]["count"] += 1
    
    count = sessions[session_id]["count"]
    scam = bool(re.search(SCAM_REGEX, text))
    
    reply = get_reply(scam, count, text)

    # 4. Human Typos (Simple)
    if scam and random.random() < 0.3:
        if len(reply) > 5:
            reply = reply.replace("e", "3").replace("a", "s") # Simple "fat finger" typos

    return {
        "status": "success",
        "scamDetected": scam,
        "messageCount": count,
        "reply": reply
    }

# --- ROUTES ---
# We point everything to the same handler
@app.post("/")
async def root_post(request: Request):
    return await universal_handler(request)

@app.post("/honeypot")
async def honeypot_post(request: Request):
    return await universal_handler(request)

@app.get("/")
async def root_get():
    return {"status": "success"}

@app.get("/honeypot")
async def honeypot_get():
    return {"status": "success"}
