from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict
import asyncio
import uuid
import os
import subprocess
import sys
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

async def ensure_browser_installed():
    """Ensure Playwright browsers are installed"""
    try:
        # Try to check if chromium is available
        playwright = await async_playwright().start()
        browser_config = get_browser_config()
        browser = await playwright.chromium.launch(**browser_config)
        await browser.close()
        await playwright.stop()
        return True
    except Exception as e:
        if "Executable doesn't exist" in str(e):
            try:
                # Try to install browsers
                result = subprocess.run([
                    sys.executable, "-m", "playwright", "install", "chromium"
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    return True
                else:
                    print(f"Browser installation failed: {result.stderr}")
                    return False
            except Exception as install_error:
                print(f"Failed to install browsers: {install_error}")
                return False
        return False
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
        if "playwright" in session:
            await session["playwright"].stop()
    sessions.clear()

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    base_url = str(request.url).rstrip('/')
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Browser Agent API - Swagger-Style Documentation</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                line-height: 1.6;
                color: #1a1a1a;
                background: #f8fafc;
                min-height: 100vh;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                min-height: 100vh;
                box-shadow: 0 0 20px rgba(0,0,0,0.05);
            }}
            
            .header {{
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
                color: white;
                padding: 2rem;
                border-bottom: 1px solid #e5e7eb;
            }}
            
            .header h1 {{
                font-size: 2.5rem;
                margin-bottom: 0.5rem;
                font-weight: 700;
            }}
            
            .header .subtitle {{
                font-size: 1.125rem;
                opacity: 0.9;
                margin-bottom: 1rem;
            }}
            
            .badges {{
                display: flex;
                gap: 0.5rem;
                flex-wrap: wrap;
            }}
            
            .badge {{
                background: rgba(255,255,255,0.2);
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 9999px;
                font-size: 0.875rem;
                font-weight: 500;
            }}
            
            .nav-tabs {{
                background: white;
                border-bottom: 1px solid #e5e7eb;
                padding: 0 2rem;
                display: flex;
                gap: 2rem;
            }}
            
            .nav-tab {{
                padding: 1rem 0;
                border-bottom: 2px solid transparent;
                color: #6b7280;
                text-decoration: none;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
            }}
            
            .nav-tab.active {{
                color: #1e40af;
                border-bottom-color: #1e40af;
            }}
            
            .content {{
                padding: 2rem;
                max-height: 70vh;
                overflow-y: auto;
            }}
            
            .tab-content {{
                display: none;
            }}
            
            .tab-content.active {{
                display: block;
            }}
            
            .endpoint-group {{
                margin-bottom: 2rem;
            }}
            
            .endpoint-group h3 {{
                color: #1f2937;
                font-size: 1.25rem;
                margin-bottom: 1rem;
                font-weight: 600;
            }}
            
            .endpoint {{
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
                overflow: hidden;
            }}
            
            .endpoint-header {{
                background: white;
                padding: 1rem;
                border-bottom: 1px solid #e5e7eb;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 1rem;
                transition: background 0.2s;
            }}
            
            .endpoint-header:hover {{
                background: #f9fafb;
            }}
            
            .method {{
                padding: 0.25rem 0.75rem;
                border-radius: 0.25rem;
                font-weight: 700;
                font-size: 0.75rem;
                text-transform: uppercase;
                min-width: 4rem;
                text-align: center;
            }}
            
            .method-get {{
                background: #10b981;
                color: white;
            }}
            
            .method-post {{
                background: #3b82f6;
                color: white;
            }}
            
            .endpoint-path {{
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-weight: 600;
                color: #1f2937;
            }}
            
            .endpoint-description {{
                color: #6b7280;
                flex: 1;
            }}
            
            .endpoint-body {{
                padding: 1rem;
                background: white;
                display: none;
            }}
            
            .endpoint-body.expanded {{
                display: block;
            }}
            
            .code-block {{
                background: #1f2937;
                color: #f3f4f6;
                padding: 1rem;
                border-radius: 0.375rem;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 0.875rem;
                overflow-x: auto;
                margin: 0.5rem 0;
                white-space: pre;
            }}
            
            .try-button {{
                background: #1e40af;
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 0.375rem;
                font-weight: 500;
                cursor: pointer;
                margin-top: 0.5rem;
                transition: background 0.2s;
            }}
            
            .try-button:hover {{
                background: #1d4ed8;
            }}
            
            .ai-section {{
                background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
                color: white;
                padding: 1.5rem;
                border-radius: 0.5rem;
                margin-bottom: 2rem;
            }}
            
            .ai-section h3 {{
                font-size: 1.25rem;


@app.get("/agent/system-check")
async def system_check():
    """Check system dependencies and Playwright installation status"""
    try:
        import subprocess
        import os
        
        # Check if we're on Render
        is_render = is_render_environment()
        
        # Check Python and pip
        python_version = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        pip_version = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, text=True)
        
        # Check Playwright installation
        playwright_check = subprocess.run([sys.executable, "-m", "playwright", "--version"], capture_output=True, text=True)
        
        # Check if chromium executable exists
        try:
            playwright = await async_playwright().start()
            browser_config = get_browser_config()
            browser = await playwright.chromium.launch(**browser_config)
            await browser.close()
            await playwright.stop()
            browser_status = "✅ Chromium available"
        except Exception as e:
            browser_status = f"❌ Chromium issue: {str(e)}"
        
        return {
            "environment": "render" if is_render else "local",
            "python_version": python_version.stdout.strip(),
            "pip_version": pip_version.stdout.strip(),
            "playwright_version": playwright_check.stdout.strip() if playwright_check.returncode == 0 else "Not installed",
            "browser_status": browser_status,
            "environment_vars": {
                "RENDER": os.getenv("RENDER"),
                "RENDER_SERVICE_ID": os.getenv("RENDER_SERVICE_ID"),
                "PORT": os.getenv("PORT")
            }
        }
    except Exception as e:
        return {"error": str(e)}


                margin-bottom: 0.5rem;
            }}
            
            .workflow-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1rem;
                margin-top: 1rem;
            }}
            
            .workflow-card {{
                background: rgba(255,255,255,0.1);
                padding: 1rem;
                border-radius: 0.375rem;
                border: 1px solid rgba(255,255,255,0.2);
            }}
            
            .workflow-card h4 {{
                margin-bottom: 0.5rem;
                font-weight: 600;
            }}
            
            .response-example {{
                background: #f0fdf4;
                border: 1px solid #bbf7d0;
                padding: 1rem;
                border-radius: 0.375rem;
                margin-top: 0.5rem;
            }}
            
            .status-indicator {{
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #10b981;
                margin-right: 0.5rem;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI Browser Agent API</h1>
                <p class="subtitle">Professional Playwright automation service designed for AI agents and developers</p>
                <div class="badges">
                    <span class="badge"><span class="status-indicator"></span>Online</span>
                    <span class="badge">FastAPI</span>
                    <span class="badge">Playwright</span>
                    <span class="badge">{'Render Cloud' if is_render_environment() else 'Local Dev'}</span>
                    <span class="badge">{'Headless Mode' if get_browser_config()["headless"] else 'Headful Mode'}</span>
                </div>
            </div>
            
            <div class="nav-tabs">
                <a href="#" class="nav-tab active" onclick="showTab('endpoints')">API Endpoints</a>
                <a href="#" class="nav-tab" onclick="showTab('ai-guide')">AI Integration</a>
                <a href="#" class="nav-tab" onclick="showTab('examples')">Examples</a>
                <a href="{base_url}/docs" target="_blank" class="nav-tab">Swagger UI</a>
            </div>
            
            <div class="content">
                <div id="endpoints" class="tab-content active">
                    <div class="ai-section">
                        <h3>🎯 Perfect for AI Agents</h3>
                        <p>This API is optimized for AI models and agents. Use natural language descriptions and the AI will understand how to interact with web pages through this service.</p>
                    </div>
                    
                    <div class="endpoint-group">
                        <h3>Browser Session Management</h3>
                        
                        <div class="endpoint">
                            <div class="endpoint-header" onclick="toggleEndpoint(this)">
                                <span class="method method-post">POST</span>
                                <span class="endpoint-path">/agent/visit</span>
                                <span class="endpoint-description">Start browser session and navigate to URL</span>
                            </div>
                            <div class="endpoint-body">
                                <p><strong>Description:</strong> Creates a new browser session and navigates to the specified URL. Returns a session_id for subsequent operations.</p>
                                <div class="code-block">curl -X POST "{base_url}/agent/visit" \\
  -H "Content-Type: application/json" \\
  -d '{{"url": "https://google.com"}}'</div>
                                <div class="response-example">
                                    <strong>Response:</strong>
                                    <div class="code-block">{{"session_id": "abc123", "message": "Visited https://google.com", "headless": true}}</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="endpoint">
                            <div class="endpoint-header" onclick="toggleEndpoint(this)">
                                <span class="method method-post">POST</span>
                                <span class="endpoint-path">/agent/close</span>
                                <span class="endpoint-description">Close browser session</span>
                            </div>
                            <div class="endpoint-body">
                                <div class="code-block">curl -X POST "{base_url}/agent/close" \\
  -H "Content-Type: application/json" \\
  -d '{{"session_id": "YOUR_SESSION_ID"}}'</div>
                            </div>
                        </div>
                        
                        <div class="endpoint">
                            <div class="endpoint-header" onclick="toggleEndpoint(this)">
                                <span class="method method-get">GET</span>
                                <span class="endpoint-path">/agent/sessions</span>
                                <span class="endpoint-description">List all active sessions</span>
                            </div>
                            <div class="endpoint-body">
                                <div class="code-block">curl "{base_url}/agent/sessions"</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="endpoint-group">
                        <h3>Page Interaction</h3>
                        
                        <div class="endpoint">
                            <div class="endpoint-header" onclick="toggleEndpoint(this)">
                                <span class="method method-post">POST</span>
                                <span class="endpoint-path">/agent/click</span>
                                <span class="endpoint-description">Click elements by CSS selector</span>
                            </div>
                            <div class="endpoint-body">
                                <div class="code-block">curl -X POST "{base_url}/agent/click" \\
  -H "Content-Type: application/json" \\
  -d '{{"session_id": "YOUR_SESSION_ID", "selector": "button.submit"}}'</div>
                            </div>
                        </div>
                        
                        <div class="endpoint">
                            <div class="endpoint-header" onclick="toggleEndpoint(this)">
                                <span class="method method-post">POST</span>
                                <span class="endpoint-path">/agent/type</span>
                                <span class="endpoint-description">Type text into form fields</span>
                            </div>
                            <div class="endpoint-body">
                                <div class="code-block">curl -X POST "{base_url}/agent/type" \\
  -H "Content-Type: application/json" \\
  -d '{{"session_id": "YOUR_SESSION_ID", "selector": "input[name=\\"search\\"]", "text": "Hello World"}}'</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="endpoint-group">
                        <h3>Page Information</h3>
                        
                        <div class="endpoint">
                            <div class="endpoint-header" onclick="toggleEndpoint(this)">
                                <span class="method method-get">GET</span>
                                <span class="endpoint-path">/agent/screenshot</span>
                                <span class="endpoint-description">Take full-page screenshot</span>
                            </div>
                            <div class="endpoint-body">
                                <div class="code-block">curl "{base_url}/agent/screenshot?session_id=YOUR_SESSION_ID"</div>
                            </div>
                        </div>
                        
                        <div class="endpoint">
                            <div class="endpoint-header" onclick="toggleEndpoint(this)">
                                <span class="method method-get">GET</span>
                                <span class="endpoint-path">/agent/info</span>
                                <span class="endpoint-description">Get page title and URL</span>
                            </div>
                            <div class="endpoint-body">
                                <div class="code-block">curl "{base_url}/agent/info?session_id=YOUR_SESSION_ID"</div>
                            </div>
                        </div>
                        
                        <div class="endpoint">
                            <div class="endpoint-header" onclick="toggleEndpoint(this)">
                                <span class="method method-get">GET</span>
                                <span class="endpoint-path">/health</span>
                                <span class="endpoint-description">Service health check</span>
                            </div>
                            <div class="endpoint-body">
                                <div class="code-block">curl "{base_url}/health"</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div id="ai-guide" class="tab-content">
                    <div class="ai-section">
                        <h3>🤖 AI Agent Integration Guide</h3>
                        <p>This service is designed to be easily consumed by AI models. Here's how to integrate it effectively:</p>
                    </div>
                    
                    <div class="workflow-grid">
                        <div class="workflow-card">
                            <h4>🎯 For AI Models</h4>
                            <p>Describe web automation tasks in natural language. The API provides simple endpoints for all common browser actions.</p>
                        </div>
                        <div class="workflow-card">
                            <h4>🔄 Session Management</h4>
                            <p>Always start with /agent/visit to get a session_id, then use it for all subsequent operations on that browser instance.</p>
                        </div>
                        <div class="workflow-card">
                            <h4>🎨 CSS Selectors</h4>
                            <p>Use standard CSS selectors for targeting elements: button, #id, .class, [attribute="value"]</p>
                        </div>
                        <div class="workflow-card">
                            <h4>📱 Cross-Platform</h4>
                            <p>Works on both local development and cloud deployment. Automatically adapts to environment.</p>
                        </div>
                    </div>
                    
                    <h3>Common AI Workflows</h3>
                    <div class="code-block">
# 1. Web scraping workflow
POST /agent/visit → GET /agent/info → GET /agent/screenshot → POST /agent/close

# 2. Form filling workflow  
POST /agent/visit → POST /agent/type → POST /agent/click → GET /agent/info → POST /agent/close

# 3. Navigation workflow
POST /agent/visit → POST /agent/click → GET /agent/screenshot → POST /agent/close
                    </div>
                </div>
                
                <div id="examples" class="tab-content">
                    <h3>🚀 Complete Examples</h3>
                    
                    <h4>Example 1: Search Google</h4>
                    <div class="code-block">
# Step 1: Visit Google
curl -X POST "{base_url}/agent/visit" \\
  -H "Content-Type: application/json" \\
  -d '{{"url": "https://google.com"}}'

# Step 2: Type in search box
curl -X POST "{base_url}/agent/type" \\
  -H "Content-Type: application/json" \\
  -d '{{"session_id": "SESSION_ID", "selector": "input[name=\\"q\\"]", "text": "OpenAI"}}'

# Step 3: Click search button
curl -X POST "{base_url}/agent/click" \\
  -H "Content-Type: application/json" \\
  -d '{{"session_id": "SESSION_ID", "selector": "input[name=\\"btnK\\"]"}}'

# Step 4: Take screenshot of results
curl "{base_url}/agent/screenshot?session_id=SESSION_ID"

# Step 5: Close session
curl -X POST "{base_url}/agent/close" \\
  -H "Content-Type: application/json" \\
  -d '{{"session_id": "SESSION_ID"}}'
                    </div>
                    
                    <h4>Example 2: JavaScript Integration</h4>
                    <div class="code-block">
async function automateWebsite(url) {{
  // Start session
  const visitResponse = await fetch('{base_url}/agent/visit', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ url }})
  }});
  const {{ session_id }} = await visitResponse.json();
  
  // Get page info
  const infoResponse = await fetch(`{base_url}/agent/info?session_id=${{session_id}}`);
  const pageInfo = await infoResponse.json();
  
  // Close session
  await fetch('{base_url}/agent/close', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ session_id }})
  }});
  
  return pageInfo;
}}
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function showTab(tabName) {{
                // Hide all tab contents
                document.querySelectorAll('.tab-content').forEach(tab => {{
                    tab.classList.remove('active');
                }});
                
                // Remove active class from all nav tabs
                document.querySelectorAll('.nav-tab').forEach(tab => {{
                    tab.classList.remove('active');
                }});
                
                // Show selected tab content
                document.getElementById(tabName).classList.add('active');
                
                // Add active class to clicked nav tab
                event.target.classList.add('active');
            }}
            
            function toggleEndpoint(header) {{
                const body = header.nextElementSibling;
                body.classList.toggle('expanded');
            }}
        </script>
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
        # Check if browsers are installed
        browser_installed = await ensure_browser_installed()
        if not browser_installed:
            raise HTTPException(
                status_code=500, 
                detail="Browser installation failed. Please ensure Playwright browsers are installed with: python -m playwright install chromium"
            )
        
        playwright = await async_playwright().start()
        browser_config = get_browser_config()
        browser = await playwright.chromium.launch(**browser_config)
        page = await browser.new_page()
        await page.goto(req.url)

        session_id = str(uuid.uuid4())
        sessions[session_id] = {"browser": browser, "page": page, "playwright": playwright}
        return {
            "session_id": session_id, 
            "message": f"Visited {req.url}",
            "headless": browser_config["headless"],
            "environment": "render" if is_render_environment() else "local"
        }
    except Exception as e:
        # More detailed error message
        error_msg = str(e)
        if "Executable doesn't exist" in error_msg:
            error_msg = "Playwright browsers not installed. Run 'python -m playwright install chromium' to fix this."
        raise HTTPException(status_code=500, detail=error_msg)

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
        session = sessions[req.session_id]
        await session["browser"].close()
        if "playwright" in session:
            await session["playwright"].stop()
        del sessions[req.session_id]
        return {"message": f"Closed session {req.session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/sessions")
def list_sessions():
    return {"active_sessions": list(sessions.keys())}
