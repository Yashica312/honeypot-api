from fastapi import FastAPI, Header, HTTPException

app = FastAPI()

# Use the same key you configured in Render
API_KEY = "mysecretkey"  # OR read from env if you want

# --------- COMMON RESPONSE ---------
def success_response():
    return {
        "status": "success",
        "scamDetected": False
    }

# --------- ENDPOINTS ---------

@app.post("/honeypot")
async def honeypot_post(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return success_response()

@app.post("/")
async def root_post(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return success_response()

@app.get("/honeypot")
async def honeypot_get():
    return success_response()

@app.get("/")
async def root_get():
    return success_response()
