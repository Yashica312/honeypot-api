from fastapi import FastAPI, Header, HTTPException
import os
import time
import re
import requests

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

sessions = {}

@app.post("/honeypot")
async def honeypot_endpoint(
    data: dict,
    x_api_key: str = Header(None)
):
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

    if (
        session["upiIds"]
        or session["phoneNumbers"]
        or session["phishingLinks"]
    ):
        should_stop = True

    # -------- Persona Reply --------
    if scam_detected and not should_stop:
        if message_count < 3:
            reply = "I don’t really understand this. Can you explain it clearly?"
        else:
            reply = "I’m helping them with this. Which bank is this from exactly?"
    elif should_stop:
        reply = "I’ll go to the bank directly tomorrow. Thank you."
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
            "agentNotes": "Scammer used urgency and payment redirection tactics"
        }

        try:
            requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
            session["callback_sent"] = True
        except Exception:
            pass  # Do not crash even if callback fails

    return {
        "status": "success",
        "scamDetected": scam_detected,
        "messageCount": message_count,
        "engagementEnded": should_stop,
        "reply": reply
    }
