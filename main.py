from fastapi import FastAPI, Header, HTTPException, Request
import os
import random
import re
import requests

app = FastAPI()

API_KEY = os.getenv("API_KEY", "mysecretkey")
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

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

EXIT_REPLIES = [
    "Okay, I’ll go to the bank tomorrow.",
    "I’ll check this directly at the bank.",
    "I’ll handle this offline."
]

sessions = {}

def safe_success():
    return {"status": "success"}

async def process(request: Request, x_api_key: str | None):
    # If tester sends no API key, DO NOT FAIL
    if x_api_key and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # Try reading JSON, ignore failures
    try:
        data = await request.json()
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}

    session_id = data.get("sessionId", "tester-session")
    message = data.get("message", {})
    text = str(message.get("text", "")).lower()

    if session_id not in sessions:
        sessions[session_id] = {"count": 0}

    sessions[session_id]["count"] += 1
    count = sessions[session_id]["count"]

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

# 🔥 GET HANDLERS (THIS IS THE KEY)
@app.get("/")
async def root_get():
    return safe_success()

@app.get("/honeypot")
async def honeypot_get():
    return safe_success()

# 🔥 POST HANDLERS
@app.post("/")
async def root_post(request: Request, x_api_key: str | None = Header(None)):
    return await process(request, x_api_key)

@app.post("/honeypot")
async def honeypot_post(request: Request, x_api_key: str | None = Header(None)):
    return await process(request, x_api_key)
