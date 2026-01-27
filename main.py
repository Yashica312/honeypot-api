from fastapi import FastAPI, Header, HTTPException

app = FastAPI()

API_KEY = "mysecretkey"

@app.post("/honeypot")
async def honeypot_endpoint(
    data: dict,
    x_api_key: str = Header(None)
):
    # Check API key
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # Dummy response for Day 1
    return {
        "status": "success",
        "scamDetected": False
    }
