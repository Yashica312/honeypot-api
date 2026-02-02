from fastapi import FastAPI, Header, HTTPException, Request
import os
import time
import re
import requests
import random

app = FastAPI()

# ================= CONFIG =================
API_KEY = os.getenv("API_KEY", "mysecretkey")
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

SCAM_KEYWORDS = [
    "account blocked",
    "verify",
    "urgent",
    "upi",
    "otp",
    "bank",
    "suspended",
    "freeze",
    "login",
    "security alert"
]

# -------- NATURAL REPLY POOLS --------
CONFUSED_REPLIES = [
    "What is this message?",
    "Why is my account blocked?",
    "I don’t understand this.",
    "I didn’t do anything wrong.",
    "This is confusing. What happened?",
    "Why am I getting this now?",
    "Can you explain what this is about?",
    "I’m not sure what this means."
]

HELPER_REPLIES = [
    "I’m helping them with this. Which bank is this?",
    "Which account are you talking about?",
    "Why is this urgent?",
    "Can you explain the issue properly?",
    "Which bank are you calling from?",
    "What exactly is the problem?",
    "Can you tell clearly what needs to be done?",
    "Why was this account flagged?"
]

EXIT_REPLIES = [
    "Okay, I’ll go to the bank tomorrow.",
    "I’ll check this directly at the bank.",
    "I’ll handle this by visiting the bank.",
    "I’ll sort this out at the bank.",
    "I’ll verify this in person tomorrow.",
    "Let me go to the bank and check.",
    "I’ll deal with this offline."
]

# ================= MEMORY =================
sessions = {}

# ================= CORE HANDLER =================
async def handle_request(request: Request, x_api_key: str):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # --- Ultra-safe body handling (tester-proof) ---
    try:
        data = await request.json()
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}

    session_id = data.get("sessionId", "tester-session")

    message = data.get("message", {})
    if not isinstance(message, dict):
        message = {}

    text = str(message.get("text", ""))
    text_lower = text.lower()

    # --- Init session ---
    if session_id not in sessions:
        sessions[session_id] = {
            "message_count": 0,
            "upiIds": set(),
            "phoneNumbers": set(),
            "phishingLinks": set(),
            "callback_sent": False
        }

    session = sessions[session_id]
    session["message_count"] += 1
    message_count = session["message_count"]

    # --- Scam detection ---
    scam_detected = any(k in text_lower for k in SCAM_KEYWORDS)

    # --- Intelligence extraction ---
    for upi in re.findall(r'\b[\w.\-]+@[\w]+\b', text_lower):
        if "upi" in upi:
            session["upiIds"].add(upi)

    for phone in re.findall(r'\b(?:\+91)?[6-9]\d{9}\b', text):
        session["phoneNumbers"].add(phone)

    for link in re.findall(r'https?://\S+', text):
        session["phishingLinks"].add(link)

    # --- Stop logic ---
    should_stop = (
        message_count >= 6
        or "otp" in text_lower
        or session["upiIds"]
        or session["phoneNumbers"]
        or session["phishingLinks"]
    )

    # --- Reply selection ---
    if scam_detected and not should_stop:
        if message_count < 3:
            reply = random.choice(CONFUSED_REPLIES)
        else:
            reply = random.choice(HELPER_REPLIES)
    elif should_stop:
        reply = random.choice(EXIT_REPLIES)
    else:
        reply = "Okay."

    # --- Mandatory callback (safe, once) ---
    if should_stop and not session["callback_sent"]:
        try:
            requests.post(
                GUVI_CALLBACK_URL,
                json={
                    "sessionId": session_id,
                    "scamDetected": scam_detected,
                    "totalMessagesExchanged": message_count,
                    "extractedIntelligence": {
                        "bankAccounts": [],
                        "upiIds": list(session["upiIds"]),
                        "phishingLinks": list(session["phishingLinks"]),
                        "phoneNumbers": list(session["phoneNumbers"]),
                        "suspiciousKeywords": []
                    },
                    "agentNotes": "Urgency-based scam interaction"
                },
                timeout=5
            )
            session["callback_sent"] = True
        except Exception:
            pass  # never crash

    return {
        "status": "success",
        "scamDetected": scam_detected,
        "messageCount": message_count,
        "engagementEnded": should_stop,
        "reply": reply
    }

# ================= ENDPOINTS =================
@app.post("/")
async def root_endpoint(request: Request, x_api_key: str = Header(None)):
    return await handle_request(request, x_api_key)

@app.post("/honeypot")
async def honeypot_endpoint(request: Request, x_api_key: str = Header(None)):
    return await handle_request(request, x_api_key)
