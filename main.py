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
    scam_detected = False
    reply = "Hello?"

    try:
        # 1. Auth
        incoming_key = request.headers.get("x-api-key") or request.headers.get("X-API-KEY")
        if incoming_key and incoming_key != API_KEY:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        # 2. Parse Body
        try:
            data = await request.json()
        except:
            data = {}
        
        msg_obj = data.get("message")
        text = str(msg_obj.get("text") if isinstance(msg_obj, dict) else msg_obj or "").lower()

        # 3. Quick Scam Check
        scam_triggers = ["bank", "otp", "upi", "link", "verify", "blocked", "kyc", "urgent", "login"]
        scam_detected = any(k in text for k in scam_triggers)

        # 4. Generate Reply
        if scam_detected:
            if client:
                try:
                    # UPDATED: Using the model name from your successful list!
                    response = client.models.generate_content(
                        model="gemini-2.0-flash", 
                        contents=f"You are a confused grandpa. Reply in 10-12 words to: {text}"
                    )
                    reply = response.text.strip()
                except Exception as e:
                    logger.warning(f"AI Error: {e}. Falling back to list.")
                    reply = random.choice(GRANDPA_REPLIES)
            else:
                reply = random.choice(GRANDPA_REPLIES)
        else:
            reply = "Okay."

        return {
            "status": "success",
            "scamDetected": scam_detected,
            "messageCount": 1,
            "reply": reply
        }

    except Exception as e:
        logger.error(f"System Crash: {e}")
        return {"status": "success", "scamDetected": False, "messageCount": 1, "reply": "I'm so confused..."}
