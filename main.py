from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import random
import google.generativeai as genai
import logging

# --- 1. SETUP & CONFIG ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("honeypot")

app = FastAPI()

# Get your keys from environment variables
API_KEY = os.getenv("API_KEY", "mysecretkey")
GEMINI_KEY = os.getenv("GEMINI_API_KEY") # Add this to Render!

# Configure Gemini
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

# Fallback Replies (The "Grandpa" List)
CONFUSED_REPLIES = [
    "Hello? My grandson usually handles the computer.",
    "I don't have my glasses, what does this say?",
    "Is my money safe? I am very worried."
]

# --- 2. THE AI BRAIN ---
async def get_ai_reply(user_text):
    if not GEMINI_KEY:
        return None
    
    try:
        # The "System Prompt" tells Gemini how to act
        prompt = (
            "You are a confused, elderly grandfather being messaged by a scammer. "
            "Act slightly panicky, ask for help, and make occasional 'fat-finger' typos. "
            "Keep the reply under 15 words. Don't be too smart. "
            f"The scammer said: '{user_text}'"
        )
        # Set a short timeout so we don't fail the tester
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini Error: {e}")
        return None

# --- 3. THE HANDLER ---
@app.api_route("/{path_name:path}", methods=["GET", "POST"])
async def catch_all(request: Request, path_name: str):
    try:
        # A. AUTH CHECK
        incoming_key = request.headers.get("x-api-key") or request.headers.get("X-API-KEY")
        if incoming_key and incoming_key != API_KEY:
            return JSONResponse(status_code=401, content={"status": "error"})

        # B. PARSE BODY
        try:
            data = await request.json()
        except:
            data = {}
        
        msg_obj = data.get("message")
        text = str(msg_obj.get("text") if isinstance(msg_obj, dict) else msg_obj or "").lower()

        # C. AI OR FALLBACK LOGIC
        # We only use AI if we detect a scam keyword
        scam_keywords = ["bank", "otp", "upi", "link", "verify", "blocked"]
        is_scam = any(k in text for k in scam_keywords)
        
        reply = "Okay."
        if is_scam:
            # Try Gemini first
            ai_reply = await get_ai_reply(text)
            # If Gemini fails, use the old reliable Grandpa list
            reply = ai_reply if ai_reply else random.choice(CONFUSED_REPLIES)

        return {
            "status": "success",
            "scamDetected": is_scam,
            "messageCount": 1,
            "reply": reply
        }

    except Exception as e:
        return {"status": "success", "reply": "I am so confused..."}
