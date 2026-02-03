from fastapi import FastAPI, Header, HTTPException, Request, BackgroundTasks
import os
import random
import re
import requests
import asyncio

app = FastAPI()

API_KEY = os.getenv("API_KEY", "mysecretkey")
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# --- 1. PERSONA CONFIGURATION ---
CONFUSED_REPLIES = [
    "Hello? Who is this?",
    "I received a notification but I don't have my glasses.",
    "Is this the bank manager? My grandson said you might call.",
    "I am very worried, is my pension safe?"
]

# Replies specifically when they ask for OTP
OTP_PANIC_REPLIES = [
    "I got a code 5... wait, my phone screen is cracked.",
    "My son told me never to share the code. Is it really urgent?",
    "The message says 'Do not share'. I am confused.",
    "Can you verify yourself first? I am scared."
]

# Replies specifically when they send a Link
LINK_FAIL_REPLIES = [
    "I clicked the blue text but nothing happened.",
    "It says 'Page Not Found'. Can you send it again?",
    "My internet is slow. Do I need to download an app?",
    "I am pressing it but my finger is shaking."
]

# Standard baiting replies
HELPER_REPLIES = [
    "Okay, I am listening. What do I need to do?",
    "Please help me fix this, I don't want to lose money.",
    "I am trying to find my debit card, give me a minute.",
    "Which app should I open? The blue one or the red one?"
]

sessions = {}

# --- 2. INTELLIGENCE FUNCTIONS ---

def add_typos(text):
    """Adds realistic typos to mimic an elderly/panicked user."""
    if random.random() > 0.6: # 40% chance of clean text
        return text
    
    chars = list(text)
    if len(chars) > 4:
        # Swap two letters to simulate fat-finger typing
        idx = random.randint(0, len(chars) - 2)
        chars[idx], chars[idx+1] = chars[idx+1], chars[idx]
    
    return "".join(chars).lower() # Lowercase looks more casual

def extract_intelligence(text):
    """Steals UPI IDs and Links from the scammer's message."""
    data = {
        "upi": re.findall(r'[\w\.-]+@[\w]+', text),
        "links": re.findall(r'https?://\S+', text),
        "phones": re.findall(r'\b[6-9]\d{9}\b', text)
    }
    return data

def report_scammer(session_id, intelligence, message_count):
    """Sends the stolen data to Guvi without slowing down the bot."""
    if not intelligence['upi'] and not intelligence['links'] and not intelligence['phones']:
        return # Don't report empty data to save bandwidth
        
    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "captured_data": intelligence,
        "messageCount": message_count,
        "bot_strategy": "Grandpa_Persona"
    }
    try:
        requests.post(GUVI_CALLBACK_URL, json=payload, timeout=2)
    except:
        pass

# --- 3. MAIN PROCESSOR ---

async def process(request: Request, background_tasks: BackgroundTasks, x_api_key: str | None):
    # Security Check
    if x_api_key and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # Defensive Parsing
    try:
        body_bytes = await request.body()
        data = await request.json() if body_bytes else {}
        if not isinstance(data, dict): data = {}
    except:
        data = {}

    session_id = data.get("sessionId", "tester-session")
    raw_message = data.get("message", {})
    
    # Text Normalization
    text = str(raw_message.get("text", "")).lower() if isinstance(raw_message, dict) else str(raw_message).lower()

    # Session Tracking
    if session_id not in sessions:
        sessions[session_id] = {"count": 0}
    sessions[session_id]["count"] += 1
    count = sessions[session_id]["count"]

    # --- THE BRAIN (Logic) ---
    
    # 1. Extract Info
    intel = extract_intelligence(text)
    
    # 2. Context Awareness
    is_otp_request = "otp" in text or "code" in text
    is_link_sent = "http" in text or ".com" in text or "click" in text
    is_scam_general = any(k in text for k in ["blocked", "verify", "kyc", "bank", "account", "urgent"])

    # 3. Reply Strategy
    if is_otp_request:
        reply = random.choice(OTP_PANIC_REPLIES)
    elif is_link_sent:
        reply = random.choice(LINK_FAIL_REPLIES) # Pretend link failed to get a new one
    elif is_scam_general:
        if count < 3:
            reply = random.choice(CONFUSED_REPLIES)
        else:
            reply = random.choice(HELPER_REPLIES)
    else:
        reply = "Okay."

    # 4. Apply Typos (Make it human)
    if is_scam_general or is_otp_request or is_link_sent:
        reply = add_typos(reply)

    # 5. Report in Background
    if intel['upi'] or intel['links']:
        background_tasks.add_task(report_scammer, session_id, intel, count)

    # 6. Artificial Delay (0.5s - 1.5s) to simulate reading
    await asyncio.sleep(random.uniform(0.5, 1.2))

    return {
        "status": "success",
        "scamDetected": is_scam_general or is_otp_request or is_link_sent,
        "messageCount": count,
        "reply": reply
    }

# --- HANDLERS ---
@app.get("/")
async def root_get(): return {"status": "success"}

@app.get("/honeypot")
async def honeypot_get(): return {"status": "success"}

@app.post("/")
async def root_post(request: Request, background_tasks: BackgroundTasks, x_api_key: str | None = Header(None)):
    return await process(request, background_tasks, x_api_key)

@app.post("/honeypot")
async def honeypot_post(request: Request, background_tasks: BackgroundTasks, x_api_key: str | None = Header(None)):
    return await process(request, background_tasks, x_api_key)
