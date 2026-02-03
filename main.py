from fastapi import FastAPI, Header, HTTPException, Request, BackgroundTasks
import os
import random
import re
import requests

app = FastAPI()

API_KEY = os.getenv("API_KEY", "mysecretkey")
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# --- SMART KEYWORDS (REGEX) ---
SCAM_REGEX = r"\b(account|blocked|verify|urgent|upi|otp|bank|suspended|click|link|reward|winner|kyc|alert)\b"

# --- PERSONA REPLIES ---
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

# --- SAFE REPORTING FUNCTION ---
def report_background(session_id, count, scam_detected, text):
    """
    This runs in the background. It attempts to send data to Guvi.
    It has a strict timeout and catches ALL errors so the main app never crashes.
    """
    try:
        # Simple extraction
        upi_list = re.findall(r'[\w\.-]+@[\w]+', text)
        link_list = re.findall(r'https?://\S+', text)
        
        # Only report if there is something interesting or it's a scam
        if scam_detected or upi_list or link_list:
            payload = {
                "sessionId": session_id,
                "scamDetected": scam_detected,
                "messageCount": count,
                "extracted_upi": upi_list,
                "extracted_links": link_list
            }
            # TIMEOUT=1 is critical. Do not wait longer than 1 second.
            requests.post(GUVI_CALLBACK_URL, json=payload, timeout=1)
    except Exception:
        # If anything fails (timeout, network error), we ignore it safely.
        pass

# --- MAIN LOGIC ---
async def process(request: Request, background_tasks: BackgroundTasks, x_api_key: str | None):
    # 1. API Key Check
    if x_api_key and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # 2. Robust Body Parsing (Fixes "Invalid Request Body")
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

    # 3. Safe Data Access
    session_id = data.get("sessionId", "tester-session")
    raw_message = data.get("message", {})
    
    text = ""
    if isinstance(raw_message, dict):
        text = str(raw_message.get("text", "")).lower()
    else:
        text = str(raw_message).lower()

    # 4. Session Tracking
    if session_id not in sessions:
        sessions[session_id] = {"count": 0}
    sessions[session_id]["count"] += 1
    count = sessions[session_id]["count"]

    # 5. Scam Logic
    scam = bool(re.search(SCAM_REGEX, text))

    if scam:
        if count < 3:
            reply = random.choice(CONFUSED_REPLIES)
        elif count < 6:
            reply = random.choice(HELPER_REPLIES)
        else:
            reply = random.choice(EXIT_REPLIES)
    else:
        reply = "Okay."

    # 6. Background Task (The "Requests" part)
    # We add this to the queue. It runs AFTER we return the response.
    background_tasks.add_task(report_background, session_id, count, scam, text)

    return {
        "status": "success",
        "scamDetected": scam,
        "messageCount": count,
        "reply": reply
    }

# --- ROUTES ---
@app.get("/")
async def root_get():
    return safe_success()

@app.get("/honeypot")
async def honeypot_get():
    return safe_success()

@app.post("/")
async def root_post(request: Request, background_tasks: BackgroundTasks, x_api_key: str | None = Header(None)):
    return await process(request, background_tasks, x_api_key)

@app.post("/honeypot")
async def honeypot_post(request: Request, background_tasks: BackgroundTasks, x_api_key: str | None = Header(None)):
    return await process(request, background_tasks, x_api_key)
