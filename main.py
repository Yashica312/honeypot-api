from fastapi import FastAPI, Header, HTTPException, Body
import os
import time
import re
import requests
import random

app = FastAPI()

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

# Reply pools (SAFE, HUMAN, NON-REVEALING)
CONFUSED_REPLIES = [
   "I’m not sure I understand this. Can you explain what’s going on?",
    "Sorry, this is a bit confusing for me. What exactly happened?",
    "I don’t really get it. What do I need to do now?",
    "Can you explain this once more? I’m not very familiar with these things.",
    "I’m confused. Why is this happening suddenly?",
    "I don’t remember doing anything wrong. Can you clarify?"
]

HELPER_REPLIES = [
    "I’m helping them with this. Which bank is this related to?",
    "Can you confirm the bank name again so we’re sure?",
    "Why is this urgent exactly? What happens if we wait?",
    "I need to understand this clearly before proceeding. Which account is affected?",
    "Can you explain the issue in detail?",
    "What is the exact problem you are seeing from your side?"
]

EXIT_REPLIES = [
    "I’ll visit the bank directly tomorrow and sort this out.",
    "I’ll check this with the bank in person. Thanks.",
    "I’ll handle this offline tomorrow.",
    "I’m going to verify this directly at the bank.",
    "I’ll get this checked tomorrow. Thank you."
]

sessions = {}

@app.post("/honeypot")
async def honeypot_endpoint(
    data: dict = Body(default={}),
    x_api_key: str = Header(None)
):
:

    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    session_id = data.get("sessionId", "unknown-session")

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

    message = data.get("message", {})
    if not isinstance(message, dict):
        message = {}
    text = message.get("text", "")
    text_lower = text.lower()

    scam_detected = any(word in text_lower for word in SCAM_KEYWORDS)

    # -------- Intelligence Extraction --------
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

    # -------- STOP LOGIC --------
    should_stop = False

    if "otp" in text_lower or "send money" in text_lower:
        should_stop = True

    if message_count >= 6:
        should_stop = True

    if session["upiIds"] or session["phoneNumbers"] or session["phishingLinks"]:
        should_stop = True

    # -------- Reply Selection --------
    if scam_detected and not should_stop:
        if message_count < 3:
            reply = random.choice(CONFUSED_REPLIES)
        else:
            reply = random.choice(HELPER_REPLIES)
    elif should_stop:
        reply = random.choice(EXIT_REPLIES)
    else:
        reply = "Okay."

    # -------- FINAL CALLBACK --------
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




