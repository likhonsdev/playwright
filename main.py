from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    base_url = "https://playwright-bqap.onrender.com"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Browser Agent API Documentation</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            
            .header {{
                background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            
            .header h1 {{
                font-size: 2.5rem;
                margin-bottom: 10px;
                font-weight: 300;
            }}
            
            .header p {{
                font-size: 1.2rem;
                opacity: 0.9;
            }}
            
            .status-badge {{
                display: inline-block;
                background: #27ae60;
                color: white;
                padding: 8px 16px;
                border-radius: 25px;
                font-size: 0.9rem;
                margin-top: 15px;
            }}
            
            .content {{
                padding: 40px;
            }}
            
            .section {{
                margin-bottom: 40px;
            }}
            
            .section h2 {{
                color: #2c3e50;
                font-size: 1.8rem;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 3px solid #3498db;
            }}
            
            .quick-links {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }}
            
            .quick-link {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                border: 2px solid transparent;
                transition: all 0.3s ease;
            }}
            
            .quick-link:hover {{
                border-color: #3498db;
                transform: translateY(-5px);
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            }}
            
            .quick-link a {{
                color: #3498db;
                text-decoration: none;
                font-weight: 600;
                font-size: 1.1rem;
            }}
            
            .quick-link p {{
                margin-top: 10px;
                color: #666;
                font-size: 0.9rem;
            }}
            
            .endpoint {{
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                border-left: 5px solid #3498db;
            }}
            
            .method {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 0.8rem;
                margin-right: 10px;
            }}
            
            .method-get {{
                background: #27ae60;
                color: white;
            }}
            
            .method-post {{
                background: #e74c3c;
                color: white;
            }}
            
            .code-block {{
                background: #2c3e50;
                color: #ecf0f1;
                padding: 15px;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                font-size: 0.9rem;
                margin: 10px 0;
                overflow-x: auto;
            }}
            
            .example-section {{
                background: #ecf0f1;
                padding: 25px;
                border-radius: 10px;
                margin-top: 30px;
            }}
            
            .step {{
                background: white;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 15px;
                border-left: 4px solid #3498db;
            }}
            
            .step h4 {{
                color: #2c3e50;
                margin-bottom: 10px;
            }}
            
            .tech-info {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }}
            
            .tech-item {{
                background: #3498db;
                color: white;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }}
            
            .tech-item strong {{
                display: block;
                font-size: 1.1rem;
                margin-bottom: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Browser Agent API</h1>
                <p>Professional browser automation service using Playwright</p>
                <div class="status-badge">✅ Online & Ready</div>
            </div>
            
            <div class="content">
                <div class="section">
                    <h2>📚 Quick Access</h2>
                    <div class="quick-links">
                        <div class="quick-link">
                            <a href="{base_url}/docs" target="_blank">📖 Interactive Docs</a>
                            <p>Swagger UI with live testing</p>
                        </div>
                        <div class="quick-link">
                            <a href="{base_url}/redoc" target="_blank">📋 ReDoc</a>
                            <p>Clean API documentation</p>
                        </div>
                        <div class="quick-link">
                            <a href="{base_url}/health" target="_blank">❤️ Health Check</a>
                            <p>Service status and info</p>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>🛠️ API Endpoints</h2>
                    
                    <div class="endpoint">
                        <span class="method method-post">POST</span>
                        <strong>/agent/visit</strong> - Start browser session and visit URL
                        <div class="code-block">curl -X POST "{base_url}/agent/visit" \\
  -H "Content-Type: application/json" \\
  -d '{{"url": "https://example.com"}}'</div>
                    </div>
                    
                    <div class="endpoint">
                        <span class="method method-get">GET</span>
                        <strong>/agent/screenshot</strong> - Take full-page screenshot
                        <div class="code-block">curl "{base_url}/agent/screenshot?session_id=YOUR_SESSION_ID"</div>
                    </div>
                    
                    <div class="endpoint">
                        <span class="method method-post">POST</span>
                        <strong>/agent/click</strong> - Click element by CSS selector
                        <div class="code-block">curl -X POST "{base_url}/agent/click" \\
  -H "Content-Type: application/json" \\
  -d '{{"session_id": "YOUR_SESSION_ID", "selector": "button"}}'</div>
                    </div>
                    
                    <div class="endpoint">
                        <span class="method method-post">POST</span>
                        <strong>/agent/type</strong> - Type text into form field
                        <div class="code-block">curl -X POST "{base_url}/agent/type" \\
  -H "Content-Type: application/json" \\
  -d '{{"session_id": "YOUR_SESSION_ID", "selector": "input", "text": "Hello"}}'</div>
                    </div>
                    
                    <div class="endpoint">
                        <span class="method method-get">GET</span>
                        <strong>/agent/info</strong> - Get page title and URL
                        <div class="code-block">curl "{base_url}/agent/info?session_id=YOUR_SESSION_ID"</div>
                    </div>
                    
                    <div class="endpoint">
                        <span class="method method-post">POST</span>
                        <strong>/agent/close</strong> - Close browser session
                        <div class="code-block">curl -X POST "{base_url}/agent/close" \\
  -H "Content-Type: application/json" \\
  -d '{{"session_id": "YOUR_SESSION_ID"}}'</div>
                    </div>
                    
                    <div class="endpoint">
                        <span class="method method-get">GET</span>
                        <strong>/agent/sessions</strong> - List all active sessions
                        <div class="code-block">curl "{base_url}/agent/sessions"</div>
                    </div>
                </div>
                
                <div class="example-section">
                    <h2>🚀 Quick Start Example</h2>
                    <div class="step">
                        <h4>Step 1: Start a browser session</h4>
                        <div class="code-block">curl -X POST "{base_url}/agent/visit" \\
  -H "Content-Type: application/json" \\
  -d '{{"url": "https://google.com"}}'</div>
                    </div>
                    
                    <div class="step">
                        <h4>Step 2: Take a screenshot</h4>
                        <div class="code-block">curl "{base_url}/agent/screenshot?session_id=RETURNED_SESSION_ID"</div>
                    </div>
                    
                    <div class="step">
                        <h4>Step 3: Close the session</h4>
                        <div class="code-block">curl -X POST "{base_url}/agent/close" \\
  -H "Content-Type: application/json" \\
  -d '{{"session_id": "RETURNED_SESSION_ID"}}'</div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>⚙️ Technical Details</h2>
                    <div class="tech-info">
                        <div class="tech-item">
                            <strong>Framework</strong>
                            FastAPI
                        </div>
                        <div class="tech-item">
                            <strong>Browser Engine</strong>
                            Chromium via Playwright
                        </div>
                        <div class="tech-item">
                            <strong>Mode</strong>
                            {'Headless' if get_browser_config()["headless"] else 'Headful'}
                        </div>
                        <div class="tech-item">
                            <strong>Platform</strong>
                            {'Render Cloud' if is_render_environment() else 'Local Dev'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

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
