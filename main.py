from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import random
import re
import logging
import sys

# --- 1. SETUP LOGGING (Crucial for debugging) ---
# This forces logs to appear in the Render Dashboard immediately
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("honeypot")

app = FastAPI()

API_KEY = os.getenv("API_KEY", "mysecretkey")

# --- 2. INTELLIGENCE CONFIG ---
SCAM_KEYWORDS = [
    "account", "blocked", "verify", "urgent", "upi", "otp", "bank", 
    "suspended", "click", "link", "reward", "winner", "kyc", "credit", "alert"
]

# Context: General Confusion
CONFUSED_REPLIES = [
    "Hello? My grandson usually handles the computer.",
    "I received a message about my bank. Is this the manager?",
    "I don't have my glasses, what does this say?",
    "Why is the bank texting me at this hour?",
    "Is my money safe? I am very worried."
]

# Context: Trying to Help
HELPER_REPLIES = [
    "Okay, I found my card. What numbers do you need?",
    "My son told me never to share the OTP, but I am scared.",
    "Do I need to come to the branch? Or can I do it here?",
    "I am trying to find the app. Which one do I download?",
    "Can you send the link again? My fingers are shaky."
]

# Context: OTP Specific
OTP_REPLIES = [
    "I see a code... is it 8-4-2... wait, it disappeared.",
    "The message says 'Do Not Share'. Should I still give it to you?",
    "I can't read the number, it's too small on this screen."
]

# Context: Link Specific
LINK_REPLIES = [
    "I clicked the blue text but it says 'Page Not Found'.",
    "Nothing is happening when I touch the link.",
    "My internet is very slow, do I need to download something?"
]

sessions = {}

# --- 3. HUMANIZER ENGINE ---
def add_typos(text):
    """Adds realistic 'old person' typos"""
    if random.random() < 0.35 and len(text) > 10:
        chars = list(text)
        idx = random.randint(0, len(chars) - 2)
        chars[idx], chars[idx+1] = chars[idx+1], chars[idx]
        return "".join(chars).lower()
    return text

# --- 4. THE BLACK BOX HANDLER ---
# Catches EVERYTHING. POST, GET, PUT to ANY URL.
@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(request: Request, path_name: str):
    
    # Default Safe Response
    response_data = {
        "status": "success",
        "scamDetected": False,
        "messageCount": 1,
        "reply": "Okay."
    }

    try:
        # A. LOGGING THE RAW INPUT
        # This will show you exactly what the tester sent in the Render Logs
        body_bytes = await request.body()
        logger.info(f"📥 INCOMING REQUEST to /{path_name}")
        logger.info(f"🔑 HEADERS: {request.headers}")
        logger.info(f"📦 BODY: {body_bytes.decode('utf-8', errors='ignore')}")

        # B. MANUAL AUTH (Soft Fail)
        incoming_key = request.headers.get("x-api-key") or request.headers.get("X-API-KEY")
        if incoming_key and incoming_key != API_KEY:
            logger.warning("⛔ Invalid API Key detected")
            # We fail gently to keep the connection alive
            return JSONResponse(status_code=401, content={"status": "error", "message": "Invalid Key"})

        # C. PARSING
        try:
            data = await request.json()
        except Exception:
            data = {}
        
        if not isinstance(data, dict):
            data = {}

        # D. EXTRACTION
        session_id = str(data.get("sessionId") or "tester-session")
        msg_obj = data.get("message")
        text = str(msg_obj.get("text") if isinstance(msg_obj, dict) else msg_obj or "").lower()

        # E. LOGIC
        if session_id not in sessions:
            sessions[session_id] = {"count": 0}
        
        sessions[session_id]["count"] += 1
        count = sessions[session_id]["count"]

        # Scam Check
        scam = False
        for k in SCAM_KEYWORDS:
            if k in text:
                scam = True
                break
        
        # Reply Logic
        reply = "Okay."
        if scam:
            if "otp" in text or "code" in text:
                reply = random.choice(OTP_REPLIES)
            elif "link" in text or "http" in text:
                reply = random.choice(LINK_REPLIES)
            elif count < 3:
                reply = random.choice(CONFUSED_REPLIES)
            else:
                reply = random.choice(HELPER_REPLIES)
            
            # Apply Typos
            reply = add_typos(reply)

        # Update Response
        response_data = {
            "status": "success",
            "scamDetected": scam,
            "messageCount": count,
            "reply": reply
        }
        
        logger.info(f"✅ REPLYING: {reply}")

    except Exception as e:
        # Catch crash, log it, return safe response
        logger.error(f"💥 CRITICAL ERROR: {e}")
        pass

    return JSONResponse(content=response_data)
