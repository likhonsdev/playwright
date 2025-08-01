from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Dict, Optional
import asyncio
import uuid
import os
import subprocess
import sys
from playwright.async_api import async_playwright

app = FastAPI(
    title="Simple Browser Agent API",
    description="Easy browser automation for AI models",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: Dict[str, object] = {}

def is_render_environment():
    return os.getenv("RENDER") is not None

def get_browser_config():
    if is_render_environment():
        return {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox", 
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--no-first-run",
                "--no-zygote",
                "--single-process"
            ]
        }
    else:
        return {"headless": False}

# Simple request models
class VisitRequest(BaseModel):
    url: str

class ClickRequest(BaseModel):
    session_id: str
    selector: str

class TypeRequest(BaseModel):
    session_id: str
    selector: str
    text: str

class CloseRequest(BaseModel):
    session_id: str

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple Browser Agent API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold; }
            .post { background: #007bff; }
            .get { background: #28a745; }
            code { background: #e9ecef; padding: 2px 4px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🤖 Simple Browser Agent API</h1>
        <p>Easy browser automation for AI models</p>

        <h2>📡 Available Endpoints</h2>

        <div class="endpoint">
            <span class="method post">POST</span> <code>/visit</code>
            <p>Start browsing a website</p>
            <pre>{"url": "https://google.com"}</pre>
        </div>

        <div class="endpoint">
            <span class="method post">POST</span> <code>/click</code>
            <p>Click an element</p>
            <pre>{"session_id": "abc123", "selector": "button"}</pre>
        </div>

        <div class="endpoint">
            <span class="method post">POST</span> <code>/type</code>
            <p>Type text into a field</p>
            <pre>{"session_id": "abc123", "selector": "input", "text": "hello"}</pre>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span> <code>/screenshot/{session_id}</code>
            <p>Take a screenshot</p>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span> <code>/sessions</code>
            <p>List active sessions</p>
        </div>

        <div class="endpoint">
            <span class="method post">POST</span> <code>/close</code>
            <p>Close a session</p>
            <pre>{"session_id": "abc123"}</pre>
        </div>

        <h2>🎯 Example Usage</h2>
        <p>1. POST /visit with {"url": "https://google.com"}</p>
        <p>2. POST /type with session_id, selector "input[name='q']", text "cats"</p>
        <p>3. POST /click with session_id, selector "input[name='btnK']"</p>
        <p>4. GET /screenshot/{session_id} to see results</p>

        <p><a href="/docs">📚 Swagger Documentation</a></p>
    </body>
    </html>
    """

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Browser Agent API is running"}

@app.post("/visit")
async def visit_page(req: VisitRequest):
    try:
        # Install browser if needed
        try:
            playwright = await async_playwright().start()
            browser_config = get_browser_config()
            browser = await playwright.chromium.launch(**browser_config)
        except Exception as e:
            if "Executable doesn't exist" in str(e):
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
                playwright = await async_playwright().start()
                browser = await playwright.chromium.launch(**browser_config)
            else:
                raise e

        page = await browser.new_page()
        await page.goto(req.url)
        title = await page.title()

        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "browser": browser, 
            "page": page, 
            "playwright": playwright,
            "url": req.url
        }

        return {
            "success": True,
            "session_id": session_id,
            "message": f"Visited {req.url}",
            "title": title
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/click")
async def click_element(req: ClickRequest):
    try:
        if req.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        page = sessions[req.session_id]["page"]
        await page.click(req.selector)

        return {
            "success": True,
            "message": f"Clicked {req.selector}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/type")
async def type_text(req: TypeRequest):
    try:
        if req.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        page = sessions[req.session_id]["page"]
        await page.fill(req.selector, req.text)

        return {
            "success": True,
            "message": f"Typed '{req.text}' into {req.selector}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/screenshot/{session_id}")
async def screenshot(session_id: str):
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        page = sessions[session_id]["page"]
        path = f"screenshot_{session_id}.png"
        await page.screenshot(path=path, full_page=True)

        return FileResponse(path, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions")
def list_sessions():
    return {
        "sessions": list(sessions.keys()),
        "count": len(sessions)
    }

@app.post("/close")
async def close_session(req: CloseRequest):
    try:
        if req.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        session = sessions[req.session_id]
        await session["browser"].close()
        await session["playwright"].stop()
        del sessions[req.session_id]

        return {
            "success": True,
            "message": f"Session {req.session_id} closed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown():
    for session in sessions.values():
        try:
            await session["browser"].close()
            await session["playwright"].stop()
        except:
            pass
    sessions.clear()