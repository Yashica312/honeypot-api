from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import random

app = FastAPI()

API_KEY = os.getenv("API_KEY", "mysecretkey")

# --- PERSONA DATABASE ---
# 1. General Confusion (The "Grandpa" baseline)
GRANDPA_REPLIES = [
    "Hello? My grandson usually handles the computer.",
    "I received a message about my bank. Is this the manager?",
    "I don't have my glasses, what does this say?",
    "Is my money safe? I am very worried."
]

# 2. OTP/Code Specific (The "Stalling" persona)
OTP_REPLIES = [
    "I see a code... is it 8-4-2... wait, it disappeared.",
    "The message says 'Do Not Share'. Should I still give it to you?",
    "I can't read the number, it's too small on this screen.",
    "My phone is vibrating, is that the code?"
]

# 3. Link/Website Specific (The "Tech-Challenged" persona)
LINK_REPLIES = [
    "I clicked the blue text but it says 'Page Not Found'.",
    "Nothing is happening when I touch the link.",
    "My internet is very slow, do I need to download something?",
    "Is this the official bank website? It looks very empty."
]

# 4. UPI/Payment Specific (The "Suspicious" persona)
UPI_REPLIES = [
    "My daughter told me never to scan random QR codes.",
    "Which app do I need for the UPI? I only have a calculator.",
    "Is this for the reward money? I really need it for my medicine."
]

@app.api_route("/{path_name:path}", methods=["GET", "POST"])
async def handle_everything(request: Request, path_name: str):
    # --- 1. AUTH ---
    incoming_key = request.headers.get("x-api-key") or request.headers.get("X-API-KEY")
    if incoming_key and incoming_key != API_KEY:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    # --- 2. THE "NO-CRASH" PARSER ---
    text = ""
    try:
        body = await request.json()
        if isinstance(body, dict):
            msg = body.get("message", "")
            # Handles both {"message": "text"} and {"message": {"text": "text"}}
            text = str(msg.get("text") if isinstance(msg, dict) else msg or "").lower()
    except:
        pass # If body is empty or not JSON, we just treat text as empty

    # --- 3. AGENTIC LOGIC ---
    scam_detected = False
    reply = "Hello?"

    # Check for keywords to trigger specific personas
    if any(k in text for k in ["bank", "verify", "blocked", "urgent", "kyc"]):
        scam_detected = True
        reply = random.choice(GRANDPA_REPLIES)
    
    if any(k in text for k in ["otp", "code", "number"]):
        scam_detected = True
        reply = random.choice(OTP_REPLIES)
        
    if any(k in text for k in ["link", "http", "click", "website"]):
        scam_detected = True
        reply = random.choice(LINK_REPLIES)

    if any(k in text for k in ["upi", "pay", "qr", "money"]):
        scam_detected = True
        reply = random.choice(UPI_REPLIES)

    # --- 4. FORMATTED RESPONSE ---
    return {
        "status": "success",
        "scamDetected": scam_detected,
        "messageCount": 1,
        "reply": reply
    }
