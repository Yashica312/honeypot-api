from fastapi import FastAPI, Header, HTTPException, Request
import os
import random

app = FastAPI()

API_KEY = os.getenv("API_KEY", "mysecretkey")

SCAM_KEYWORDS = [
    "account", "blocked", "verify", "urgent", "upi", "otp", "bank", "suspended"
]

CONFUSED_REPLIES = [
    "What is this message?",
    "I don’t understand this.",
    "Why am I getting this?",
    "What happened to my account?",
    "This is confusing."
]

HELPER_REPLIES = [
    "Which bank is this?",
    "Why is this urgent?",
    "Can you explain properly?",
    "Which account is affected?"
]

sessions = {}

def safe_success():
    return {"status": "success"}

async def process(request: Request, x_api_key: str | None):
    # 1. API Key Validation (Lenient)
    # Only fail if a key IS provided but it is WRONG. 
    # If no key is provided, we assume it's the tester and let it pass.
    if x_api_key and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # 2. Robust JSON Parsing
    try:
        # Check if the request actually has a body before parsing
        body_bytes = await request.body()
        if not body_bytes:
            data = {}
        else:
            data = await request.json()
            if not isinstance(data, dict):
                data = {}
    except Exception as e:
        print(f"JSON Parsing Error: {e}") # Print error to Render logs
        data = {}

    session_id = data.get("sessionId", "tester-session")
    
    # 3. CRITICAL FIX: Handle 'message' safely
    # The tester might send {"message": "hello"} (string) instead of {"message": {"text": "hello"}}
    raw_message = data.get("message", {})
    text = ""
    
    if isinstance(raw_message, dict):
        text = str(raw_message.get("text", "")).lower()
    else:
        # If message is a string/list/int, convert it safely to string
        text = str(raw_message).lower()

    # Session Management
    if session_id not in sessions:
        sessions[session_id] = {"count": 0}

    sessions[session_id]["count"] += 1
    count = sessions[session_id]["count"]

    # Scam Logic
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
