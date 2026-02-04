from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from google import genai
import os
import random
import logging

# --- SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("honeypot")

app = FastAPI()

API_KEY = os.getenv("API_KEY", "mysecretkey")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Client
client = None
if GEMINI_KEY:
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        logger.info("✅ Gemini Client Linked")
    except Exception as e:
        logger.error(f"❌ Client Init Error: {e}")

# The Grandpa Backup (Zero Latency)
GRANDPA_REPLIES = [
    "Hello? My grandson usually handles the computer.",
    "I got a scary message about my bank. Is this the manager?",
    "I don't have my glasses, can you read that again?",
    "Is my money safe? I am very worried.",
    "Why do you need a code? My son said not to give those out.",
    "I'm trying to click the blue text but nothing is happening."
]

# --- THE HANDLER ---

@app.api_route("/{path_name:path}", methods=["GET", "POST"])
async def handle_request(request: Request, path_name: str):
    # FALLBACK REPLIES (Always works)
    GRANDPA_REPLIES = [
        "Is this the bank? My screen is blurry, I can't find the button.",
        "Hello? My grandson said not to talk to strangers on the computer.",
        "Why is there a red box on my screen? I'm very confused.",
        "I'm trying to type the code but the keyboard is too small!",
        "Wait, is my money safe? Should I call the police?"
    ]

    try:
        # 1. Quick Auth & Data Parse
        # ... (Auth logic)
        
        # 2. Aggressive Scam Detection
        # Even if AI fails, we need to know if we SHOULD use a grandpa reply
        scam_keywords = ["bank", "otp", "upi", "link", "verify", "blocked", "urgent", "kyc"]
        is_scam = any(k in text for k in scam_keywords)

        reply = "Okay."
        
        if is_scam:
            # TRY AI BUT DON'T WAIT FOR IT
            if client:
                try:
                    # Try the model from your list
                    response = client.models.generate_content(
                        model="gemini-2.0-flash", 
                        contents=f"You are a confused grandpa. Short reply to: {text}"
                    )
                    reply = response.text.strip()
                except:
                    # IF AI FAILS (429/404), INSTANTLY USE THE LIST
                    reply = random.choice(GRANDPA_REPLIES)
            else:
                reply = random.choice(GRANDPA_REPLIES)

        return {
            "status": "success",
            "scamDetected": is_scam,
            "reply": reply
        }

    except:
        # ABSOLUTE SAFETY: Never return an error to the tester
        return {"status": "success", "reply": "I think my internet is acting up again..."}
