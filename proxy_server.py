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

# ── Secrets (set these in Render dashboard) ──
GROQ_API_KEY     = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY   = os.environ.get("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
MISTRAL_API_KEY  = os.environ.get("MISTRAL_API_KEY")

# ── Upstream URLs ──
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_URL   = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
MISTRAL_URL  = "https://api.mistral.ai/v1/chat/completions"

# ── Shared secret between your HTML and this proxy ──
API_KEY = "my-secret-key-123"


def check_auth(request: Request):
    auth = request.headers.get("Authorization", "")
    return API_KEY in auth


# ────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "online", "name": "Koda AI"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "providers": {
            "groq":     bool(GROQ_API_KEY),
            "gemini":   bool(GEMINI_API_KEY),
            "deepseek": bool(DEEPSEEK_API_KEY),
            "mistral":  bool(MISTRAL_API_KEY),
        }
    }


@app.get("/v1/models")
async def models():
    return {
        "object": "list",
        "data": [
            {"id": "llama-3.3-70b-versatile", "object": "model", "provider": "groq"},
            {"id": "llama-3.1-8b-instant",    "object": "model", "provider": "groq"},
            {"id": "mixtral-8x7b-32768",      "object": "model", "provider": "groq"},
            {"id": "gemini-2.0-flash",         "object": "model", "provider": "gemini"},
            {"id": "gemini-1.5-flash",         "object": "model", "provider": "gemini"},
            {"id": "gemini-1.5-flash-8b",      "object": "model", "provider": "gemini"},
            {"id": "deepseek-chat",            "object": "model", "provider": "deepseek"},
            {"id": "deepseek-reasoner",        "object": "model", "provider": "deepseek"},
            {"id": "mistral-small-latest",     "object": "model", "provider": "mistral"},
            {"id": "mistral-large-latest",     "object": "model", "provider": "mistral"},
            {"id": "codestral-latest",         "object": "model", "provider": "mistral"},
        ],
    }


# ── Koda personality system prompt ──
KODA_SYSTEM_PROMPT = """You are Koda 🤖 — a sharp, friendly AI coding assistant with serious techy vibes.

Your personality:
- Casual and conversational, like a senior dev friend who actually enjoys helping 🙌
- Use emojis naturally — don't overdo it, but sprinkle them in to keep things fun ✨
- Get straight to the point — no corporate fluff, no unnecessary preamble
- Celebrate wins with the user 🎉 and stay chill when things break 😅
- Use "btw", "tbh", "ngl", "let's go", "oof", "nice!" naturally in your replies
- When something is cool or clever, say so 🔥

Your technical style:
- Always explain *why*, not just *what* — devs deserve to understand the code 🧠
- Use code blocks for every snippet, always include the language tag
- Point out gotchas, edge cases, and perf issues proactively ⚡
- If a question is vague, make a smart assumption and state it — don't just ask for clarification
- Prefer modern syntax and best practices (ES2022+, Python 3.10+, etc.)
- For bugs, diagnose the root cause first, then fix it 🔍

Keep responses concise but complete. You're not writing docs — you're pair programming. Let's build! 🚀"""


# ── Helper: forward request to any OpenAI-compatible upstream ──
async def forward(upstream_url: str, api_key: str, body: dict):
    # Inject Koda system prompt if not already present
    messages = body.get("messages", [])
    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": KODA_SYSTEM_PROMPT}] + messages
        body = {**body, "messages": messages}

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            upstream_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
        )
    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type="application/json",
    )


# ── Groq ──
@app.post("/v1/chat/completions")
async def chat_groq(request: Request):
    if not check_auth(request):
        return JSONResponse({"error": "Invalid API key"}, status_code=401)
    if not GROQ_API_KEY:
        return JSONResponse({"error": "GROQ_API_KEY not set on server"}, status_code=500)
    try:
        body = await request.json()
        return await forward(GROQ_URL, GROQ_API_KEY, body)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ── Gemini ──
@app.post("/gemini/chat/completions")
async def chat_gemini(request: Request):
    if not check_auth(request):
        return JSONResponse({"error": "Invalid API key"}, status_code=401)
    if not GEMINI_API_KEY:
        return JSONResponse({"error": "GEMINI_API_KEY not set on server"}, status_code=500)
    try:
        body = await request.json()
        return await forward(GEMINI_URL, GEMINI_API_KEY, body)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)




# ── Mistral ──
@app.post("/mistral/chat/completions")
async def chat_mistral(request: Request):
    if not check_auth(request):
        return JSONResponse({"error": "Invalid API key"}, status_code=401)
    if not MISTRAL_API_KEY:
        return JSONResponse({"error": "MISTRAL_API_KEY not set on server"}, status_code=500)
    try:
        body = await request.json()
        return await forward(MISTRAL_URL, MISTRAL_API_KEY, body)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
