from fastapi import FastAPI, Header, HTTPException, Request, BackgroundTasks
import os
import random
import re
import requests
import time
import asyncio

app = FastAPI()

# ================= CONFIGURATION =================
API_KEY = os.getenv("API_KEY", "mysecretkey")
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# Extended Keyword List
SCAM_KEYWORDS = [
    "account", "blocked", "verify", "urgent", "upi", "otp", "bank", 
    "suspended", "kyc", "click", "link", "reward", "winner", "update", 
    "freeze", "pan card", "adhar", "credit card"
]

# ================= THE "GRANDPA" PERSONA =================
# We mimic an elderly person to make the scammer frustrated but persistent
CONFUSED_REPLIES = [
    "Hello? My grandson usually handles the computer.",
    "I received a message about my bank. Is this the manager?",
    "I don't have my glasses, what does this say?",
    "Why is the bank texting me at this hour?",
    "Is my money safe? I am very worried."
]

BAITING_REPLIES = [
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

# ================= MEMORY STORAGE =================
sessions = {}

def safe_success():
    return {"status": "success"}

# ================= BACKGROUND TASK (REPORTING) =================
def report_to_guvi(session_id: str, session_data: dict):
    """
    Sends the gathered intelligence to the callback URL.
    This runs in the background to avoid slowing down the chat.
    """
    try:
        payload = {
            "sessionId": session_id,
            "scamDetected": True,
            "totalMessagesExchanged": session_data["count"],
            "extractedIntelligence": {
                "upiIds": list(session_data["upiIds"]),
                "phishingLinks": list(session_data["phishingLinks"]),
                "phoneNumbers": list(session_data["phoneNumbers"]),
            },
            "agentNotes": "Persona: Elderly Victim. Strategy: Wasting time."
        }
        
        # Send data (Timeout set to 5s so we don't hang if Guvi is down)
        requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
        print(f"✅ REPORTED Session {session_id} with {len(session_data['phishingLinks'])} links.")
    except Exception as e:
        print(f"❌ REPORT FAILED: {e}")

# ================= MAIN LOGIC =================
async def process(request: Request, x_api_key: str | None, background_tasks: BackgroundTasks):
    # 1. Security Check
    if x_api_key and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # 2. Defensive JSON Parsing
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

    # 3. Data Extraction
    session_id = data.get("sessionId", "tester-session")
    raw_message = data.get("message", {})
    
    # Handle text safely (whether it's dict, string, or None)
    if isinstance(raw_message, dict):
        text = str(raw_message.get("text", "")).lower()
    else:
        text = str(raw_message).lower()

    # 4. Session Initialization
    if session_id not in sessions:
        sessions[session_id] = {
            "count": 0,
            "upiIds": set(),
            "phoneNumbers": set(),
            "phishingLinks": set()
        }
    
    session = sessions[session_id]
    session["count"] += 1

    # 5. INTELLIGENCE GATHERING (Regex)
    # Extract UPI IDs
    found_upis = re.findall(r'[\w\.-]+@[\w]+', text)
    session["upiIds"].update(found_upis)

    # Extract Phone Numbers (India format mostly)
    found_phones = re.findall(r'\b(?:\+91)?[6-9]\d{9}\b', text)
    session["phoneNumbers"].update(found_phones)

    # Extract Links
    found_links = re.findall(r'https?://\S+', text)
    session["phishingLinks"].update(found_links)

    # 6. Scam Detection & Reply Logic
    scam = any(k in text for k in SCAM_KEYWORDS)
    should_stop = session["count"] >= 6 or (scam and len(found_links) > 0)

    # Simulate typing delay (Humanize)
    await asyncio.sleep(random.uniform(0.2, 0.8))

    if not scam:
        reply = "Okay."
    elif should_stop:
        reply = random.choice(EXIT_REPLIES)
        # If we are stopping and have data, report it now
        if len(session["upiIds"]) > 0 or len(session["phishingLinks"]) > 0:
            background_tasks.add_task(report_to_guvi, session_id, session)
    elif session["count"] < 3:
        reply = random.choice(CONFUSED_REPLIES)
    else:
        reply = random.choice(BAITING_REPLIES)

    return {
        "status": "success",
        "scamDetected": scam,
        "messageCount": session["count"],
        "extracted_data": {
            "upi": list(session["upiIds"]),
            "links": list(session["phishingLinks"])
        },
        "reply": reply
    }

# ================= ENDPOINTS =================
@app.get("/")
async def root_get():
    return safe_success()

@app.get("/honeypot")
async def honeypot_get():
    return safe_success()

@app.post("/")
async def root_post(request: Request, background_tasks: BackgroundTasks, x_api_key: str | None = Header(None)):
    return await process(request, x_api_key, background_tasks)

@app.post("/honeypot")
async def honeypot_post(request: Request, background_tasks: BackgroundTasks, x_api_key: str | None = Header(None)):
    return await process(request, x_api_key, background_tasks)
