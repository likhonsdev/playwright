from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import asyncio
import uuid
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

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/agent/visit")
async def visit_page(req: VisitRequest):
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(req.url)

        session_id = str(uuid.uuid4())
        sessions[session_id] = {"browser": browser, "page": page}
        return {"session_id": session_id, "message": f"Visited {req.url}"}
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
