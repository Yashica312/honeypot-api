from fastapi import FastAPI, Header, HTTPException, Request, BackgroundTasks
import os
import random
import re
import requests

app = FastAPI()

API_KEY = os.getenv("API_KEY", "mysecretkey")
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# 1. SMARTER KEYWORDS (Regex Patterns)
# We use \b to ensure we match whole words only.
SCAM_PATTERNS = [
    r"\baccount\b", r"\bblocked\b", r"\bverify\b", r"\burgent\b", 
    r"\bupi\b", r"\botp\b", r"\bbank\b", r"\bsuspended\b", 
    r"\bclick\b", r"\blink\b", r"\breward\b", r"\bkyc\b"
]

# 2. GRANDPA REPLIES
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

# 3. TYPO GENERATOR (Humanizer)
def add_typos(text):
    if random.random() > 0.7: # 30% chance to not make typos
        return text
    
    # Simple typo logic: double a letter or swap chars
    chars = list(text)
    if len(chars) > 5:
        idx = random.randint(0, len(chars) - 2)
        # Swap two characters (e.g., "bank" -> "bnak")
        chars[idx], chars[idx+1] = chars[idx+1], chars[idx]
    return "".join(chars)

# 4. BACKGROUND REPORTING
def send_report(session_id, message_count, scam_status):
    try:
        payload = {
            "sessionId": session_id,
            "scamDetected": scam_status,
            "messageCount": message_count,
            "notes": "Grandpa Persona Active"
        }
        # Timeout is crucial so we don't hang
        requests.post(GUVI_CALLBACK_URL, json=payload, timeout=3)
    except Exception:
        pass # Fail silently, don't crash the server

async def process(request: Request, background_tasks: BackgroundTasks, x_api_key: str | None):
    # --- SAFETY CHECK ---
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

    # --- SMARTER DETECTION ---
    scam = False
    for pattern in SCAM_PATTERNS:
        if re.search(pattern, text):
            scam = True
            break

    # --- SELECT REPLY ---
    if scam and count < 3:
        reply = random.choice(CONFUSED_REPLIES)
    elif scam:
        reply = random.choice(HELPER_REPLIES)
    else:
        reply = "Okay."

    # --- HUMAN TOUCH ---
    # Add typos to the reply if it's a scam message (Grandpa is panicking)
    if scam:
        reply = add_typos(reply)

    # --- INVISIBLE REPORTING ---
    # This runs AFTER the return, so the tester gets the response instantly
    if scam:
        background_tasks.add_task(send_report, session_id, count, scam)

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

# POST HANDLERS (Added background_tasks)
@app.post("/")
async def root_post(request: Request, background_tasks: BackgroundTasks, x_api_key: str | None = Header(None)):
    return await process(request, background_tasks, x_api_key)

@app.post("/honeypot")
async def honeypot_post(request: Request, background_tasks: BackgroundTasks, x_api_key: str | None = Header(None)):
    return await process(request, background_tasks, x_api_key)
