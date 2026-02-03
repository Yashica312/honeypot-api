from fastapi import FastAPI, Header, HTTPException, Request
import os
import random
import re

app = FastAPI()

API_KEY = os.getenv("API_KEY", "mysecretkey")

# --- SMART KEYWORDS (REGEX) ---
# Detects whole words like "bank" but ignores "bankrupt" or "banking" if needed.
SCAM_REGEX = r"\b(account|blocked|verify|urgent|upi|otp|bank|suspended|click|link|reward|winner|kyc|alert)\b"

# --- PERSONA: THE CONFUSED GRANDPA ---
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

# --- HUMAN TOUCH (TYPOS) ---
def humanize_text(text):
    # 30% chance to swap letters to look like a real human typing fast
    if random.random() < 0.3 and len(text) > 5:
        chars = list(text)
        idx = random.randint(0, len(chars) - 2)
        chars[idx], chars[idx+1] = chars[idx+1], chars[idx]
        return "".join(chars)
    return text

# --- MAIN PROCESSOR ---
async def process(request: Request, x_api_key: str | None):
    # 1. API Key Validation
    if x_api_key and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # 2. Crash-Proof JSON Parsing
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
    
    text = ""
    if isinstance(raw_message, dict):
        text = str(raw_message.get("text", "")).lower()
    else:
        text = str(raw_message).lower()

    if session_id not in sessions:
        sessions[session_id] = {"count": 0}

    sessions[session_id]["count"] += 1
    count = sessions[session_id]["count"]

    # 4. Smart Logic (Regex)
    scam = bool(re.search(SCAM_REGEX, text))

    # 5. Reply Strategy
    if scam:
        if "otp" in text:
            # Special reply for OTPs
            reply = "I see a code but I cannot read it clearly. Is it 5 digits?"
        elif "link" in text or "http" in text:
            # Special reply for Links
            reply = "I clicked the blue text but it says Page Not Found."
        elif count < 3:
            reply = random.choice(CONFUSED_REPLIES)
        elif count < 6:
            reply = random.choice(HELPER_REPLIES)
        else:
            reply = random.choice(EXIT_REPLIES)
        
        # Add realistic typos
        reply = humanize_text(reply)
    else:
        reply = "Okay."

    return {
        "status": "success",
        "scamDetected": scam,
        "messageCount": count,
        "reply": reply
    }

# --- HANDLERS ---
@app.get("/")
async def root_get():
    return safe_success()

@app.get("/honeypot")
async def honeypot_get():
    return safe_success()

@app.post("/")
async def root_post(request: Request, x_api_key: str | None = Header(None)):
    return await process(request, x_api_key)

@app.post("/honeypot")
async def honeypot_post(request: Request, x_api_key: str | None = Header(None)):
    return await process(request, x_api_key)
