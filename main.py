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
    "suspended"
]

CONFUSED_REPLIES = [
    "What is this? I don’t understand.",
    "Why is my account blocked?",
    "I didn’t do anything. What happened?",
    "I’m confused, what should I do now?",
    "This message is not clear to me.",
    "Why am I getting this message suddenly?"
]

HELPER_REPLIES = [
    "I’m helping them with this. Which bank is this?",
    "Can you tell clearly which account this is about?",
    "Why is this urgent?",
    "What exactly is the issue here?",
    "Which bank are you calling from?",
    "Please explain the problem properly."
]

EXIT_REPLIES = [
    "Okay, I’ll go to the bank tomorrow.",
    "I’ll check this at the bank directly.",
    "I’ll handle this by visiting the bank.",
    "I’ll see this tomorrow at the bank.",
    "Let me go to the bank and check."
]

# ================= MEMORY =================
sessions = {}

# ================= ENDPOINT =================
@app.post("/honeypot")
async def honeypot_endpoint(
    request: Request,
    x_api_key: str = Header(None)
):
    # ---- Auth check ----
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # ---- Safely read body (TESTER-PROOF) ----
    try:
        data = await request.json()
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}

    session_id = data.get("sessionId", "unknown-session")

    message = data.get("message", {})
    if not isinstance(message, dict):
        message = {}

    text = str(message.get("text", ""))
    text_lower = text.lower()

    # ---- Init session ----
    if session_id not in sessions:
        sessions[session_id] = {
            "message_count": 0,
            "start_time": time.time(),
            "upiIds": set(),
            "phoneNumbers": set(),
            "phishingLinks": set(),
            "suspiciousKeywords": set(),
            "callback_sent": False
        }

    session = sessions[session_id]
    session["message_count"] += 1
    message_count = session["message_count"]

    # ---- Scam detection ----
    scam_detected = any(word in text_lower for word in SCAM_KEYWORDS)

    # ---- Intelligence extraction ----
    upi_matches = re.findall(r'\b[\w.\-]+@[\w]+\b', text_lower)
    for upi in upi_matches:
        if "upi" in upi:
            session["upiIds"].add(upi)

    phone_matches = re.findall(r'\b(?:\+91)?[6-9]\d{9}\b', text)
    for phone in phone_matches:
        session["phoneNumbers"].add(phone)

    link_matches = re.findall(r'https?://\S+', text)
    for link in link_matches:
        session["phishingLinks"].add(link)

    for word in SCAM_KEYWORDS:
        if word in text_lower:
            session["suspiciousKeywords"].add(word)

    # ---- Stop logic ----
    should_stop = False

    if "otp" in text_lower or "send money" in text_lower:
        should_stop = True

    if message_count >= 6:
        should_stop = True

    if session["upiIds"] or session["phoneNumbers"] or session["phishingLinks"]:
        should_stop = True

    # ---- Reply selection ----
    if scam_detected and not should_stop:
        if message_count < 3:
            reply = random.choice(CONFUSED_REPLIES)
        else:
            reply = random.choice(HELPER_REPLIES)
    elif should_stop:
        reply = random.choice(EXIT_REPLIES)
    else:
        reply = "Okay."

    # ---- Mandatory callback ----
    if should_stop and not session["callback_sent"]:
        payload = {
            "sessionId": session_id,
            "scamDetected": scam_detected,
            "totalMessagesExchanged": message_count,
            "extractedIntelligence": {
                "bankAccounts": [],
                "upiIds": list(session["upiIds"]),
                "phishingLinks": list(session["phishingLinks"]),
                "phoneNumbers": list(session["phoneNumbers"]),
                "suspiciousKeywords": list(session["suspiciousKeywords"])
            },
            "agentNotes": "Urgency-based scam with payment redirection"
        }

        try:
            requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
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
