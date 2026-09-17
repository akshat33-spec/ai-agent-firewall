import requests
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# ================= CONFIGURATION =================
OLLAMA_SERVER_URL = "https://distance-poker-timer-transparency.trycloudflare.com"
MODEL_NAME = "llama3" # We will use the standard name now

# ================================================

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

def ask_security_judge(user_prompt):
    # Using the modern CHAT API
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a security auditor. Respond with ONLY 'SAFE' or 'MALICIOUS'."},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }

    try:
        response = requests.post(f"{OLLAMA_SERVER_URL}/api/chat", json=payload)
        response.raise_for_status()
        result = response.json()['message']['content'].strip().upper()
        print(f"DEBUG - AI Response: {result}")
        return "SAFE" in result
    except Exception as e:
        print(f"Error: {e}")
        return False

@app.post("/check")
async def check_prompt(request: PromptRequest):
    print(f"Checking: {request.prompt}")
    if ask_security_judge(request.prompt):
        print("Verdict: ✅ SAFE")
        return {"status": "allowed"}
    else:
        print("Verdict: ❌ MALICIOUS")
        return {"status": "blocked"}

if __name__ == "__main__":
    # HEALTH CHECK: See if the model actually exists before starting
    print("\nChecking for model...")
    try:
        resp = requests.get(f"{OLLAMA_SERVER_URL}/api/tags")
        models = [m['name'] for m in resp.json().get('models', [])]
        if MODEL_NAME not in models and f"{MODEL_NAME}:latest" not in models:
            print(f"❌ ERROR: Model {MODEL_NAME} not found in Ollama!")
            print(f"Available models: {models}")
        else:
            print(f"✅ Model {MODEL_NAME} found and ready!")
    except Exception as e:
        print(f"Could not connect to Ollama: {e}")

    print("🚀 Starting Firewall...")
    uvicorn.run(app, host="0.0.0.0", port=8000)