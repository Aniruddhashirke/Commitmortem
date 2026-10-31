"""Gemma 4 client. Uses the Gemini API when GEMINI_API_KEY is set, else returns None
so callers fall back to deterministic offline behaviour (demo works without network)."""
import json, os, urllib.request
BASE = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={k}"
def available(): return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("OLLAMA_URL"))
def generate(prompt, fast=False, system=None, timeout=30):
    try:
        if os.environ.get("GEMINI_API_KEY"):
            model = os.environ.get("GEMMA_FAST_MODEL" if fast else "GEMMA_REASONING_MODEL",
                                   "gemma-4-26b-a4b-it" if fast else "gemma-4-31b-it")
            body = {"contents": [{"parts": [{"text": (system + "\n\n" if system else "") + prompt}]}]}
            req = urllib.request.Request(BASE.format(m=model, k=os.environ["GEMINI_API_KEY"]),
                  json.dumps(body).encode(), {"Content-Type": "application/json"})
            r = json.load(urllib.request.urlopen(req, timeout=timeout))
            return "".join(p.get("text", "") for p in r["candidates"][0]["content"]["parts"]).strip()
        if os.environ.get("OLLAMA_URL"):
            body = {"model": os.environ.get("OLLAMA_MODEL", "gemma3"), "prompt": (system or "") + "\n\n" + prompt, "stream": False}
            req = urllib.request.Request(os.environ["OLLAMA_URL"].rstrip("/") + "/api/generate",
                  json.dumps(body).encode(), {"Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=timeout))["response"].strip()
    except Exception as e:
        print("[gemma] falling back to offline mode:", e)
    return None
