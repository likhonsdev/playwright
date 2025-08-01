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
    base_url = "https://playwright-bqap.onrender.com" if is_render_environment() else "http://localhost:5000"
    return {
        "service": "Browser Agent API",
        "description": "Professional browser automation service using Playwright",
        "version": "1.0.0",
        "status": "online",
        "environment": "production" if is_render_environment() else "development",
        "base_url": base_url,
        
        "documentation": {
            "interactive_swagger": f"{base_url}/docs",
            "redoc_documentation": f"{base_url}/redoc",
            "health_check": f"{base_url}/health"
        },
        
        "endpoints": [
            {
                "method": "GET",
                "path": "/",
                "description": "API documentation and status"
            },
            {
                "method": "GET", 
                "path": "/health",
                "description": "Service health check"
            },
            {
                "method": "POST",
                "path": "/agent/visit", 
                "description": "Start browser session and visit URL",
                "example": {
                    "url": f"{base_url}/agent/visit",
                    "body": {"url": "https://example.com"},
                    "curl": f'curl -X POST "{base_url}/agent/visit" -H "Content-Type: application/json" -d \'{{"url": "https://example.com"}}\''
                }
            },
            {
                "method": "POST",
                "path": "/agent/click",
                "description": "Click element by CSS selector", 
                "example": {
                    "url": f"{base_url}/agent/click",
                    "body": {"session_id": "uuid", "selector": "button"},
                    "curl": f'curl -X POST "{base_url}/agent/click" -H "Content-Type: application/json" -d \'{{"session_id": "YOUR_SESSION_ID", "selector": "button"}}\''
                }
            },
            {
                "method": "POST", 
                "path": "/agent/type",
                "description": "Type text into form field",
                "example": {
                    "url": f"{base_url}/agent/type",
                    "body": {"session_id": "uuid", "selector": "input", "text": "Hello World"},
                    "curl": f'curl -X POST "{base_url}/agent/type" -H "Content-Type: application/json" -d \'{{"session_id": "YOUR_SESSION_ID", "selector": "input", "text": "Hello World"}}\''
                }
            },
            {
                "method": "GET",
                "path": "/agent/screenshot",
                "description": "Take full-page screenshot",
                "example": {
                    "url": f"{base_url}/agent/screenshot?session_id=YOUR_SESSION_ID",
                    "curl": f'curl "{base_url}/agent/screenshot?session_id=YOUR_SESSION_ID"'
                }
            },
            {
                "method": "GET",
                "path": "/agent/info", 
                "description": "Get page title and URL",
                "example": {
                    "url": f"{base_url}/agent/info?session_id=YOUR_SESSION_ID",
                    "curl": f'curl "{base_url}/agent/info?session_id=YOUR_SESSION_ID"'
                }
            },
            {
                "method": "POST",
                "path": "/agent/close",
                "description": "Close browser session",
                "example": {
                    "url": f"{base_url}/agent/close",
                    "body": {"session_id": "uuid"},
                    "curl": f'curl -X POST "{base_url}/agent/close" -H "Content-Type: application/json" -d \'{{"session_id": "YOUR_SESSION_ID"}}\''
                }
            },
            {
                "method": "GET",
                "path": "/agent/sessions",
                "description": "List all active sessions", 
                "example": {
                    "url": f"{base_url}/agent/sessions",
                    "curl": f'curl "{base_url}/agent/sessions"'
                }
            }
        ],
        
        "quick_start": {
            "step_1": f'curl -X POST "{base_url}/agent/visit" -H "Content-Type: application/json" -d \'{{"url": "https://google.com"}}\'',
            "step_2": f'curl "{base_url}/agent/screenshot?session_id=RETURNED_SESSION_ID"',
            "step_3": f'curl -X POST "{base_url}/agent/close" -H "Content-Type: application/json" -d \'{{"session_id": "RETURNED_SESSION_ID"}}\''
        },
        
        "technical_details": {
            "framework": "FastAPI",
            "browser_engine": "Chromium via Playwright", 
            "mode": "headless" if get_browser_config()["headless"] else "headful",
            "deployment": "Render Cloud Platform" if is_render_environment() else "Local Development"
        }
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

class CloseRequest(BaseModel):
    session_id: str

@app.post("/agent/close")
async def close_browser(req: CloseRequest):
    try:
        await sessions[req.session_id]["browser"].close()
        del sessions[req.session_id]
        return {"message": f"Closed session {req.session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/sessions")
def list_sessions():
    return {"active_sessions": list(sessions.keys())}
