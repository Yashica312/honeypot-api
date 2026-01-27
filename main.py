from fastapi import FastAPI, Header, HTTPException
import os

app = FastAPI()

# Read API key from environment (Render-safe)
API_KEY = os.getenv("API_KEY", "mysecretkey")

# Simple scam keywords
SCAM_KEYWORDS = [
    "account blocked",
    "verify",
    "urgent",
    "upi",
    "otp",
    "bank",
    "suspended"
]

@app.post("/honeypot")
async def honeypot_endpoint(
    data: dict,
    x_api_key: str = Header(None)
):
    # 1. API key check
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # 2. Safely read incoming message text
    message = data.get("message", {})
    text = message.get("text", "")
    text_lower = text.lower()

    # 3. Detect scam intent (simple rules)
    scam_detected = False
    for word in SCAM_KEYWORDS:
        if word in text_lower:
            scam_detected = True
            break

    # 4. Human-like reply
    if scam_detected:
        reply = "I’m not sure what this means, can you explain it properly?"
    else:
        reply = "Okay."

    # 5. Return response
    return {
        "status": "success",
        "scamDetected": scam_detected,
        "reply": reply
    }
