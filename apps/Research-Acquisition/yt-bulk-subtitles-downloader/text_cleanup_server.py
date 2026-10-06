#!/usr/bin/env python3
"""Text cleanup server — listens on localhost:10790
Receives messy text, returns clean well-formed English via DeepSeek API.

Usage:
  1. Set your API key: set DEEPSEEK_API_KEY=sk-...
  2. python text_cleanup_server.py
  3. AHK sends selected text here, gets clean text back

POF 2828 | July 2026
"""
import json
import os
import sys
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 10790

# DeepSeek API — fast and cheap
API_URL = "https://api.deepseek.com/chat/completions"
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = "deepseek-v4-flash"
MAX_CHUNK = 15000  # characters per chunk — v4-flash handles massive context
MAX_TOKENS = 16384  # response token cap — plenty for any cleanup job
TIMEOUT = 120     # seconds

SYSTEM_PROMPT = """This is rough voice-to-text from a speaker who thinks in connected systems. The transmission is noisy but the signal is coherent. Your job is to find the coherent structure underneath the incoherent delivery.

Rules:
- Sentences that repeat are one sentence trying to form — find its final shape
- Tangents that seem unrelated are connections forming — if the connection is real, make it visible. If it's a false start, cut it
- The speaker often delivers the conclusion before the setup — that's not an error. Restructure so the reader gets setup then conclusion, but don't lose the conclusion
- Never add ideas the speaker didn't say
- Never soften the speaker's claims
- Never hedge what they stated plainly
- Do not add commentary, greetings, or explanations
- Do not wrap in quotes or markdown
- Keep the same tone and register — if casual, stay casual. If intense, stay intense
- Aim for half the original length
- Output ONLY the cleaned text, nothing else
- The test: read it back to the speaker and they should say 'yeah, that's what I meant'"""


def chunk_text(text, max_chars=MAX_CHUNK):
    """Split text into chunks at paragraph boundaries, falling back to sentence boundaries."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    paragraphs = text.split('\n\n')

    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            # If single paragraph is too big, split on sentences
            if len(para) > max_chars:
                sentences = para.replace('. ', '.\n').split('\n')
                sub = ""
                for s in sentences:
                    if len(sub) + len(s) + 1 <= max_chars:
                        sub = (sub + " " + s).strip()
                    else:
                        if sub:
                            chunks.append(sub)
                        sub = s
                if sub:
                    chunks.append(sub)
                current = ""
            else:
                current = para
    if current:
        chunks.append(current)

    return chunks if chunks else [text]


def call_deepseek(text):
    if not API_KEY:
        return "[ERROR: Set DEEPSEEK_API_KEY environment variable]"

    chunks = chunk_text(text)
    results = []

    for i, chunk in enumerate(chunks):
        context = ""
        if len(chunks) > 1:
            context = f"\n\n[This is chunk {i+1} of {len(chunks)}. Maintain continuity with previous chunks.]"

        payload = json.dumps({
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT + context},
                {"role": "user", "content": chunk}
            ],
            "max_tokens": MAX_TOKENS,
            "temperature": 0.1,
            "stream": False
        }).encode("utf-8")

        req = urllib.request.Request(API_URL, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        })

        try:
            resp = urllib.request.urlopen(req, timeout=TIMEOUT)
            data = json.loads(resp.read().decode("utf-8"))
            results.append(data["choices"][0]["message"]["content"].strip())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            results.append(f"[API ERROR {e.code}: {body[:200]}]")
        except Exception as e:
            results.append(f"[ERROR: {str(e)[:200]}]")

    return "\n\n".join(results)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        if self.path != "/clean":
            self.send_response(404)
            self.end_headers()
            return

        n = int(self.headers.get("Content-Length", 0))
        text = self.rfile.read(n).decode("utf-8", errors="replace").strip()

        if not text:
            self._respond(400, "empty input")
            return

        clean = call_deepseek(text)
        self._respond(200, clean)

    def _respond(self, code, text):
        data = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    if not API_KEY:
        print("WARNING: DEEPSEEK_API_KEY not set!")
        print("  set DEEPSEEK_API_KEY=sk-your-key-here")
        print("  then restart this script")
        print()

    print(f"Text Cleanup Server -> http://127.0.0.1:{PORT}/clean")
    print(f"Model: {MODEL}")
    print(f"API Key: {'SET' if API_KEY else 'MISSING'}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
