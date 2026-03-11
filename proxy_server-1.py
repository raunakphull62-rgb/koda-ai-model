import os
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="Koda AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY = "my-secret-key-123"


@app.get("/")
async def root():
    return {"status": "online", "name": "Koda AI"}


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
        ],
    }


@app.post("/v1/chat/completions")
async def chat(request: Request):
    auth = request.headers.get("Authorization", "")
    if API_KEY not in auth:
        return JSONResponse({"error": "Invalid API key"}, status_code=401)
    if not GROQ_API_KEY:
        return JSONResponse({"error": "GROQ_API_KEY not set on server"}, status_code=500)
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                GROQ_URL,
                headers={
                    "Authorization": "Bearer " + GROQ_API_KEY,
                    "Content-Type": "application/json",
                },
                json=body,
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                media_type="application/json",
            )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
