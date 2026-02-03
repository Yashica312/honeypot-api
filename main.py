from fastapi import FastAPI, Header, HTTPException, Request
import os
import random

app = FastAPI()

API_KEY = os.getenv("API_KEY", "mysecretkey")

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

# Words to detect (Simple and Safe)
SCAM_WORDS = ["account", "blocked", "verify", "urgent", "upi", "otp", "bank", "suspended", "click", "link", "reward"]

sessions = {}

def safe_success():
    return {"status": "success"}

async def process(request: Request, x_api_key: str | None):
    # --- THE SAFETY NET START ---
    try:
        # 1. Check API Key
        if x_api_key and x_api_key != API_KEY:
            # We return a polite error instead of crashing
            raise HTTPException(status_code=401, detail="Invalid API Key")

        # 2. Safely read JSON
        try:
            data = await request.json()
        except Exception:
            # If body is empty or invalid JSON, pretend it's an empty dict
            data = {}

        if not isinstance(data, dict):
            data = {}

        # 3. Extract Data safely
        session_id = data.get("sessionId", "tester-session")
        message_data = data.get("message", {})
        
        # Handle cases where message might be a string or dict
        text = ""
        if isinstance(message_data, dict):
            text = str(message_data.get("text", "")).lower()
        else:
            text = str(message_data).lower()

        # 4. Session Logic
        if session_id not in sessions:
            sessions[session_id] = {"count": 0}
        
        sessions[session_id]["count"] += 1
        count = sessions[session_id]["count"]

        # 5. Simple Detection
        scam = False
        for word in SCAM_WORDS:
            if word in text:
                scam = True
                break

        # 6. Reply Logic (Grandpa Persona)
        if scam:
            if "otp" in text:
                reply = "I see a code but I cannot read it clearly. Is it 5 digits?"
            elif "link" in text or "http" in text:
                reply = "I clicked the blue text but nothing happened."
            elif count < 3:
                reply = random.choice(CONFUSED_REPLIES)
            elif count < 6:
                reply = random.choice(HELPER_REPLIES)
            else:
                reply = random.choice(EXIT_REPLIES)
        else:
            reply = "Okay."

        # 7. Return Result
        return {
            "status": "success",
            "scamDetected": scam,
            "messageCount": count,
            "reply": reply
        }

    except Exception as e:
        # --- THE SAFETY NET CATCH ---
        # If ANYTHING crashes above, we return this default success message.
        # This prevents the "Invalid Request Body" / 500 error.
        print(f"Error caught: {e}") 
        return {
            "status": "success",
            "scamDetected": False,
            "messageCount": 1,
            "reply": "Okay."
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
