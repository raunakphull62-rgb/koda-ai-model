from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import httpx
import os

app = FastAPI(title="Koda AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ API key loaded from Render environment — never in code
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY = "my-secret-key-123"

LANDING_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Koda AI</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: #0a0a0f;
      color: #fff;
      font-family: 'Segoe UI', sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
    }
    .card {
      text-align: center;
      padding: 48px;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 24px;
      max-width: 420px;
    }
    .logo {
      font-size: 52px;
      font-weight: 700;
      letter-spacing: -2px;
      margin-bottom: 8px;
      background: linear-gradient(135deg, #fff 0%, #888 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .tagline { color: rgba(255,255,255,0.4); font-size: 14px; margin-bottom: 32px; }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 20px;
      background: rgba(34,197,94,0.1);
      border: 1px solid rgba(34,197,94,0.2);
      border-radius: 999px;
      font-size: 13px;
      color: #22c55e;
    }
    .dot {
      width: 8px; height: 8px;
      background: #22c55e;
      border-radius: 50%;
      animation: pulse 2s infinite;
    }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">Koda</div>
    <div class="tagline">AI Coding Assistant — Powered by Groq</div>
    <div class="status"><div class="dot"></div> Server Online</div>
  </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(LANDING_PAGE)

@app.get("/health")
async def health():
    return {"status": "healthy", "model": "llama-3.3-70b-versatile", "provider": "groq"}

@app.get("/v1/models")
async def models():
    return {
        "object": "list",
        "data": [
            {"id": "llama-3.3-70b-versatile", "object": "model"},
            {"id": "llama-3.1-8b-instant", "object": "model"},
            {"id": "mixtral-8x7b-32768", "object": "model"},
            {"id": "gemma2-9b-it", "object": "model"},
        ]
    }

@app.post("/v1/chat/completions")
async def chat(request: Request):
    auth = request.headers.get("Authorization", "")
    if API_KEY not in auth:
        return JSONResponse({"error": "Invalid API key"}, status_code=401)

    if not GROQ_API_KEY:
        return JSONResponse({"error": "GROQ_API_KEY not set in environment"}, status_code=500)

    try:
        body = await request.json()

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                media_type="application/json",
            )
    except httpx.TimeoutException:
        return JSONResponse({"error": "Request timed out"}, status_code=504)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
