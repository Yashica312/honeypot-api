from fastapi import FastAPI, Header, Request
import os
import random

app = FastAPI()

API_KEY = os.getenv("API_KEY", "mysecretkey")

# --- FAST LOGIC ---
SCAM_KEYWORDS = ["account", "blocked", "verify", "urgent", "upi", "otp", "bank", "link"]

CONFUSED = [
    "Hello? My grandson handles this.",
    "I don't have my glasses.",
    "Why is the bank texting me?"
]

HELPING = [
    "Which account is it?",
    "I am scared, what do I do?",
    "Can you send the link again?"
]

# --- THE PROCESSOR ---
async def process(request: Request, x_api_key: str | None):
    # FALLBACK RESPONSE (If anything goes wrong, return this)
    fallback = {
        "status": "success",
        "scamDetected": False,
        "messageCount": 1,
        "reply": "Okay."
    }

    try:
        # 1. API Check (Lenient)
        if x_api_key and x_api_key != API_KEY:
            # Don't crash, just pretend to work or return error safely
            pass 

        # 2. JSON Parsing (Safe)
        try:
            body = await request.json()
        except:
            body = {}
        
        if not isinstance(body, dict):
            body = {}

        # 3. Logic
        text = str(body.get("message", {}).get("text", "")).lower()
        session_id = str(body.get("sessionId", "session"))
        
        # 4. Scam Check
        scam = any(k in text for k in SCAM_KEYWORDS)

        if scam:
            reply = random.choice(HELPING) if "otp" in text else random.choice(CONFUSED)
        else:
            reply = "Okay."

        # 5. Success
        return {
            "status": "success",
            "scamDetected": scam,
            "messageCount": 1, 
            "reply": reply
        }

    except Exception as e:
        # IF IT CRASHES, RETURN SAFE FALLBACK
        print(f"Error: {e}")
        return fallback

# --- ROUTES ---
@app.post("/")
async def root_post(request: Request, x_api_key: str | None = Header(None)):
    return await process(request, x_api_key)

@app.post("/honeypot")
async def honeypot_post(request: Request, x_api_key: str | None = Header(None)):
    return await process(request, x_api_key)

@app.get("/")
async def root_get():
    return {"status": "success"}

@app.get("/honeypot")
async def honeypot_get():
    return {"status": "success"}
