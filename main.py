from fastapi import FastAPI, Header, HTTPException
import os
import time
import re

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

# In-memory session store
sessions = {}

@app.post("/honeypot")
async def honeypot_endpoint(
    data: dict,
    x_api_key: str = Header(None)
):
    # API key check
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    session_id = data.get("sessionId", "unknown-session")

    # Initialize session if new
    if session_id not in sessions:
        sessions[session_id] = {
            "message_count": 0,
            "start_time": time.time(),
            "upiIds": set(),
            "phoneNumbers": set(),
            "phishingLinks": set(),
            "suspiciousKeywords": set()
        }

    session = sessions[session_id]

    # Update message count
    session["message_count"] += 1
    message_count = session["message_count"]

    # Read message text
    message = data.get("message", {})
    text = message.get("text", "")
    text_lower = text.lower()

    # Scam detection
    scam_detected = any(word in text_lower for word in SCAM_KEYWORDS)

    # -------------------------------
    # 🧠 INTELLIGENCE EXTRACTION
    # -------------------------------

    # Extract UPI IDs
    upi_matches = re.findall(r'\b[\w.\-]+@[\w]+\b', text_lower)
    for upi in upi_matches:
        if "upi" in upi:
            session["upiIds"].add(upi)

    # Extract phone numbers (India)
    phone_matches = re.findall(r'\b(?:\+91)?[6-9]\d{9}\b', text)
    for phone in phone_matches:
        session["phoneNumbers"].add(phone)

    # Extract links
    link_matches = re.findall(r'https?://\S+', text)
    for link in link_matches:
        session["phishingLinks"].add(link)

    # Extract suspicious keywords
    for word in SCAM_KEYWORDS:
        if word in text_lower:
            session["suspiciousKeywords"].add(word)

    # -------------------------------
    # PERSONA SWITCHING (Day 5)
    # -------------------------------
    if scam_detected:
        if message_count < 3:
            reply = "I don’t really understand this. Can you explain it clearly?"
        else:
            reply = "I’m helping them with this. Which bank is this from exactly?"
    else:
        reply = "Okay."

    # -------------------------------
    # Response (convert sets to lists)
    # -------------------------------
    return {
        "status": "success",
        "scamDetected": scam_detected,
        "messageCount": message_count,
        "extractedIntelligence": {
            "upiIds": list(session["upiIds"]),
            "phoneNumbers": list(session["phoneNumbers"]),
            "phishingLinks": list(session["phishingLinks"]),
            "suspiciousKeywords"
