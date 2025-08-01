from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import asyncio
import uuid
import os
from playwright.async_api import async_playwright

app = FastAPI()

# CORS for Netlify/Render communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with frontend origin for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: Dict[str, object] = {}  # Store browser sessions

def is_render_environment():
    """Detect if running on Render platform"""
    return os.getenv("RENDER") is not None or os.getenv("RENDER_SERVICE_ID") is not None

def get_browser_config():
    """Get browser configuration based on environment"""
    if is_render_environment():
        # Render requires headless mode and specific args
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
        # Local development - can use headful mode
        return {"headless": False}
class VisitRequest(BaseModel):
    url: str

class ClickRequest(BaseModel):
    session_id: str
    selector: str

class TypeRequest(BaseModel):
    session_id: str
    selector: str
    text: str

@app.on_event("shutdown")
async def shutdown_sessions():
    for session in sessions.values():
        await session["browser"].close()
    sessions.clear()

@app.get("/")
def root():
    return {
        "title": "🤖 Browser Agent API",
        "description": "FastAPI-based browser automation service using Playwright",
        "version": "1.0.0",
        "status": "✅ Running",
        "environment": "🌐 Render" if is_render_environment() else "🏠 Local",
        "mode": "🔒 Headless" if get_browser_config()["headless"] else "👁️ Headful",
        
        "📚 API Documentation": {
            "interactive_docs": "/docs",
            "redoc": "/redoc"
        },
        
        "🛠️ Available Endpoints": {
            "GET /": "Show this documentation",
            "GET /health": "Health check with environment info",
            "POST /agent/visit": "Launch browser and visit a URL",
            "POST /agent/click": "Click on elements by selector",
            "POST /agent/type": "Fill form fields with text",
            "GET /agent/screenshot": "Take a full-page screenshot",
            "GET /agent/info": "Get page title and URL",
            "POST /agent/close": "Close browser session",
            "GET /agent/sessions": "List all active sessions"
        },
        
        "📝 Usage Examples": {
            "start_session": {
                "method": "POST",
                "url": "/agent/visit",
                "body": {"url": "https://example.com"},
                "response": {"session_id": "uuid", "message": "Visited https://example.com"}
            },
            "take_screenshot": {
                "method": "GET", 
                "url": "/agent/screenshot?session_id=YOUR_SESSION_ID",
                "response": {"screenshot_path": "session_id.png"}
            },
            "click_element": {
                "method": "POST",
                "url": "/agent/click",
                "body": {"session_id": "YOUR_SESSION_ID", "selector": "button"},
                "response": {"message": "Clicked button"}
            },
            "type_text": {
                "method": "POST",
                "url": "/agent/type", 
                "body": {"session_id": "YOUR_SESSION_ID", "selector": "input", "text": "Hello"},
                "response": {"message": "Typed into input"}
            }
        },
        
        "🔧 Environment Details": {
            "platform": "render" if is_render_environment() else "local",
            "headless_mode": get_browser_config()["headless"],
            "browser_args": get_browser_config().get("args", "default")
        },
        
        "💡 Tips": [
            "Visit /docs for interactive Swagger UI documentation",
            "All POST requests require Content-Type: application/json",
            "Session IDs are required for most operations after visiting a page",
            "Screenshots are saved with session_id.png filename",
            "Always close sessions when done to free resources"
        ]
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "environment": "render" if is_render_environment() else "local",
        "headless_mode": get_browser_config()["headless"]
    }

@app.post("/agent/visit")
async def visit_page(req: VisitRequest):
    try:
        playwright = await async_playwright().start()
        browser_config = get_browser_config()
        browser = await playwright.chromium.launch(**browser_config)
        page = await browser.new_page()
        await page.goto(req.url)

        session_id = str(uuid.uuid4())
        sessions[session_id] = {"browser": browser, "page": page}
        return {
            "session_id": session_id, 
            "message": f"Visited {req.url}",
            "headless": browser_config["headless"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/click")
async def click_element(req: ClickRequest):
    try:
        page = sessions[req.session_id]["page"]
        await page.click(req.selector)
        return {"message": f"Clicked {req.selector}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/type")
async def type_text(req: TypeRequest):
    try:
        page = sessions[req.session_id]["page"]
        await page.fill(req.selector, req.text)
        return {"message": f"Typed into {req.selector}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/screenshot")
async def screenshot(session_id: str):
    try:
        page = sessions[session_id]["page"]
        path = f"{session_id}.png"
        await page.screenshot(path=path, full_page=True)
        return {"screenshot_path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/info")
async def get_info(session_id: str):
    try:
        page = sessions[session_id]["page"]
        title = await page.title()
        url = page.url
        return {"title": title, "url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/close")
async def close_browser(session_id: str):
    try:
        await sessions[session_id]["browser"].close()
        del sessions[session_id]
        return {"message": f"Closed session {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/sessions")
def list_sessions():
    return {"active_sessions": list(sessions.keys())}
