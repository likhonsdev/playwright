
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import uuid
import os
import subprocess
import sys
import json
from playwright.async_api import async_playwright

app = FastAPI(
    title="AI Browser Agent API",
    description="Professional browser automation service designed for AI agents",
    version="2.0.0"
)

# CORS for AI model integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: Dict[str, object] = {}

def is_render_environment():
    """Detect if running on Render platform"""
    return os.getenv("RENDER") is not None or os.getenv("RENDER_SERVICE_ID") is not None

def get_browser_config():
    """Get browser configuration based on environment"""
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
                "--single-process",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor"
            ]
        }
    else:
        return {"headless": False}

async def ensure_browser_installed():
    """Ensure Playwright browsers are installed"""
    try:
        playwright = await async_playwright().start()
        browser_config = get_browser_config()
        browser = await playwright.chromium.launch(**browser_config)
        await browser.close()
        await playwright.stop()
        return True
    except Exception as e:
        if "Executable doesn't exist" in str(e):
            try:
                result = subprocess.run([
                    sys.executable, "-m", "playwright", "install", "chromium"
                ], capture_output=True, text=True, timeout=300)
                return result.returncode == 0
            except:
                return False
        return False

# Enhanced request models for AI agents
class VisitRequest(BaseModel):
    url: str
    wait_for_load: bool = True
    timeout: int = 30000

class ClickRequest(BaseModel):
    session_id: str
    selector: str
    wait_for_element: bool = True
    timeout: int = 5000

class TypeRequest(BaseModel):
    session_id: str
    selector: str
    text: str
    clear_first: bool = True
    wait_for_element: bool = True

class ScrollRequest(BaseModel):
    session_id: str
    direction: str = "down"  # up, down, left, right
    pixels: int = 500

class WaitRequest(BaseModel):
    session_id: str
    selector: Optional[str] = None
    timeout: int = 5000

class ExtractRequest(BaseModel):
    session_id: str
    selector: str
    attribute: Optional[str] = None  # text, href, src, etc.

class CloseRequest(BaseModel):
    session_id: str

@app.on_event("shutdown")
async def shutdown_sessions():
    for session in sessions.values():
        try:
            await session["browser"].close()
            if "playwright" in session:
                await session["playwright"].stop()
        except:
            pass
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
        <title>AI Browser Agent API - Perfect for Gemini & AI Models</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                line-height: 1.6;
                color: #1a1a1a;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                min-height: 100vh;
                box-shadow: 0 0 30px rgba(0,0,0,0.1);
            }}
            
            .header {{
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
                color: white;
                padding: 3rem 2rem;
                text-align: center;
            }}
            
            .header h1 {{
                font-size: 3rem;
                margin-bottom: 1rem;
                font-weight: 800;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }}
            
            .header .subtitle {{
                font-size: 1.25rem;
                opacity: 0.95;
                margin-bottom: 1.5rem;
                max-width: 600px;
                margin-left: auto;
                margin-right: auto;
            }}
            
            .badges {{
                display: flex;
                gap: 1rem;
                justify-content: center;
                flex-wrap: wrap;
            }}
            
            .badge {{
                background: rgba(255,255,255,0.2);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 2rem;
                font-weight: 600;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.3);
            }}
            
            .nav-tabs {{
                background: white;
                border-bottom: 2px solid #e5e7eb;
                padding: 0 2rem;
                display: flex;
                gap: 3rem;
                overflow-x: auto;
            }}
            
            .nav-tab {{
                padding: 1.5rem 0;
                border-bottom: 3px solid transparent;
                color: #6b7280;
                text-decoration: none;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                white-space: nowrap;
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
                animation: fadeIn 0.3s ease-in;
            }}
            
            .tab-content.active {{
                display: block;
            }}
            
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            .ai-hero {{
                background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
                color: white;
                padding: 2rem;
                border-radius: 1rem;
                margin-bottom: 2rem;
                text-align: center;
            }}
            
            .ai-hero h2 {{
                font-size: 2rem;
                margin-bottom: 1rem;
            }}
            
            .feature-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
            }}
            
            .feature-card {{
                background: #f8fafc;
                padding: 1.5rem;
                border-radius: 0.75rem;
                border: 1px solid #e2e8f0;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            
            .feature-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            }}
            
            .feature-card h3 {{
                color: #1e40af;
                margin-bottom: 0.5rem;
                font-size: 1.25rem;
            }}
            
            .endpoint-group {{
                margin-bottom: 2.5rem;
            }}
            
            .endpoint-group h3 {{
                color: #1f2937;
                font-size: 1.5rem;
                margin-bottom: 1.5rem;
                font-weight: 700;
                border-bottom: 2px solid #e5e7eb;
                padding-bottom: 0.5rem;
            }}
            
            .endpoint {{
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 0.75rem;
                margin-bottom: 1rem;
                overflow: hidden;
                transition: box-shadow 0.2s;
            }}
            
            .endpoint:hover {{
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
            
            .endpoint-header {{
                background: #f9fafb;
                padding: 1.5rem;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 1rem;
                transition: background 0.2s;
            }}
            
            .endpoint-header:hover {{
                background: #f3f4f6;
            }}
            
            .method {{
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                font-weight: 800;
                font-size: 0.875rem;
                text-transform: uppercase;
                min-width: 5rem;
                text-align: center;
                color: white;
            }}
            
            .method-get {{ background: #10b981; }}
            .method-post {{ background: #3b82f6; }}
            
            .endpoint-path {{
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-weight: 700;
                color: #1f2937;
                font-size: 1.1rem;
            }}
            
            .endpoint-description {{
                color: #6b7280;
                flex: 1;
                font-weight: 500;
            }}
            
            .endpoint-body {{
                padding: 1.5rem;
                background: white;
                display: none;
                border-top: 1px solid #e5e7eb;
            }}
            
            .endpoint-body.expanded {{
                display: block;
            }}
            
            .code-block {{
                background: #1f2937;
                color: #f3f4f6;
                padding: 1.5rem;
                border-radius: 0.5rem;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 0.875rem;
                overflow-x: auto;
                margin: 1rem 0;
                white-space: pre;
                border: 1px solid #374151;
            }}
            
            .response-example {{
                background: #f0fdf4;
                border: 1px solid #bbf7d0;
                padding: 1.5rem;
                border-radius: 0.5rem;
                margin-top: 1rem;
            }}
            
            .gemini-section {{
                background: linear-gradient(135deg, #4285f4 0%, #34a853 100%);
                color: white;
                padding: 2rem;
                border-radius: 1rem;
                margin: 2rem 0;
            }}
            
            .live-demo {{
                background: #fef3c7;
                border: 1px solid #f59e0b;
                padding: 1.5rem;
                border-radius: 0.5rem;
                margin: 1rem 0;
            }}
            
            .status-indicator {{
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: #10b981;
                margin-right: 0.5rem;
                animation: pulse 2s infinite;
            }}
            
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
                100% {{ opacity: 1; }}
            }}
            
            .try-button {{
                background: #1e40af;
                color: white;
                border: none;
                padding: 0.75rem 1.5rem;
                border-radius: 0.5rem;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.2s;
                margin-top: 1rem;
            }}
            
            .try-button:hover {{
                background: #1d4ed8;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI Browser Agent API</h1>
                <p class="subtitle">Perfect for Gemini, ChatGPT, Claude & all AI models - Human-like browser automation with advanced capabilities</p>
                <div class="badges">
                    <span class="badge"><span class="status-indicator"></span>Live & Running</span>
                    <span class="badge">Gemini Ready</span>
                    <span class="badge">AI Optimized</span>
                    <span class="badge">{'Render Cloud' if is_render_environment() else 'Local Dev'}</span>
                </div>
            </div>
            
            <div class="nav-tabs">
                <a href="#" class="nav-tab active" onclick="showTab('overview')">🎯 AI Overview</a>
                <a href="#" class="nav-tab" onclick="showTab('endpoints')">📡 API Endpoints</a>
                <a href="#" class="nav-tab" onclick="showTab('gemini')">🔮 Gemini Examples</a>
                <a href="#" class="nav-tab" onclick="showTab('workflows')">🚀 AI Workflows</a>
                <a href="{base_url}/docs" target="_blank" class="nav-tab">📚 Swagger UI</a>
            </div>
            
            <div class="content">
                <div id="overview" class="tab-content active">
                    <div class="ai-hero">
                        <h2>🎯 Built Specifically for AI Agents</h2>
                        <p>This API enables AI models to browse the web like humans - click, type, scroll, extract data, and take screenshots with simple API calls.</p>
                    </div>
                    
                    <div class="feature-grid">
                        <div class="feature-card">
                            <h3>🧠 AI-First Design</h3>
                            <p>Every endpoint is designed for AI consumption with clear responses and error handling.</p>
                        </div>
                        <div class="feature-card">
                            <h3>🎭 Human-like Actions</h3>
                            <p>Scroll, wait for elements, extract text, handle timeouts - just like a human would.</p>
                        </div>
                        <div class="feature-card">
                            <h3>🔮 Gemini Compatible</h3>
                            <p>Optimized for Google's Gemini with detailed examples and clear documentation.</p>
                        </div>
                        <div class="feature-card">
                            <h3>📱 Cloud Ready</h3>
                            <p>Runs perfectly on Render cloud with headless Chrome for production use.</p>
                        </div>
                        <div class="feature-card">
                            <h3>🛡️ Error Resilient</h3>
                            <p>Handles network timeouts, missing elements, and browser crashes gracefully.</p>
                        </div>
                        <div class="feature-card">
                            <h3>⚡ High Performance</h3>
                            <p>Session management, parallel operations, and optimized for speed.</p>
                        </div>
                    </div>
                    
                    <div class="gemini-section">
                        <h3>🤖 Perfect for AI Agents</h3>
                        <p><strong>Tell your AI model:</strong> "Use the Browser Agent API at {base_url} to browse websites. Start with POST /agent/visit, then use other endpoints to interact with pages like a human would."</p>
                        <br>
                        <p><strong>Key Features:</strong></p>
                        <ul style="margin-left: 2rem; margin-top: 0.5rem;">
                            <li>✅ Visit any website and get session ID</li>
                            <li>✅ Click buttons, links, and elements</li>
                            <li>✅ Fill forms and type text</li>
                            <li>✅ Scroll pages in any direction</li>
                            <li>✅ Extract text and data from elements</li>
                            <li>✅ Take full-page screenshots</li>
                            <li>✅ Wait for dynamic content to load</li>
                            <li>✅ Handle multiple browser sessions</li>
                        </ul>
                    </div>
                </div>
                
                <div id="endpoints" class="tab-content">
                    <div class="endpoint-group">
                        <h3>🌐 Session Management</h3>
                        
                        <div class="endpoint">
                            <div class="endpoint-header" onclick="toggleEndpoint(this)">
                                <span class="method method-post">POST</span>
                                <span class="endpoint-path">/agent/visit</span>
                                <span class="endpoint-description">Start browser session and visit URL</span>
                            </div>
                            <div class="endpoint-body">
                                <p><strong>Perfect for:</strong> Starting any web browsing task</p>
                                <div class="code-block">curl -X POST "{base_url}/agent/visit" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "url": "https://google.com",
    "wait_for_load": true,
    "timeout": 30000
  }}'</div>
                                <div class="response-example">
                                    <strong>Response:</strong>
                                    <div class="code-block">{{"session_id": "abc123", "message": "Visited https://google.com", "title": "Google"}}</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="endpoint">
                            <div class="endpoint-header" onclick="toggleEndpoint(this)">
                                <span class="method method-get">GET</span>
                                <span class="endpoint-path">/agent/sessions</span>
                                <span class="endpoint-description">List all active browser sessions</span>
                            </div>
                            <div class="endpoint-body">
                                <div class="code-block">curl "{base_url}/agent/sessions"</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="endpoint-group">
                        <h3>🖱️ Human-like Interactions</h3>
                        
                        <div class="endpoint">
                            <div class="endpoint-header" onclick="toggleEndpoint(this)">
                                <span class="method method-post">POST</span>
                                <span class="endpoint-path">/agent/click</span>
                                <span class="endpoint-description">Click any element (buttons, links, etc.)</span>
                            </div>
                            <div class="endpoint-body">
                                <div class="code-block">curl -X POST "{base_url}/agent/click" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "session_id": "YOUR_SESSION_ID",
    "selector": "button.search-btn",
    "wait_for_element": true,
    "timeout": 5000
  }}'</div>
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
  -d '{{
    "session_id": "YOUR_SESSION_ID",
    "selector": "input[name=\\"q\\"]",
    "text": "AI browser automation",
    "clear_first": true
  }}'</div>
                            </div>
                        </div>
                        
                        <div class="endpoint">
                            <div class="endpoint-header" onclick="toggleEndpoint(this)">
                                <span class="method method-post">POST</span>
                                <span class="endpoint-path">/agent/scroll</span>
                                <span class="endpoint-description">Scroll page in any direction</span>
                            </div>
                            <div class="endpoint-body">
                                <div class="code-block">curl -X POST "{base_url}/agent/scroll" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "session_id": "YOUR_SESSION_ID",
    "direction": "down",
    "pixels": 500
  }}'</div>
                            </div>
                        </div>
                        
                        <div class="endpoint">
                            <div class="endpoint-header" onclick="toggleEndpoint(this)">
                                <span class="method method-post">POST</span>
                                <span class="endpoint-path">/agent/wait</span>
                                <span class="endpoint-description">Wait for elements or page changes</span>
                            </div>
                            <div class="endpoint-body">
                                <div class="code-block">curl -X POST "{base_url}/agent/wait" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "session_id": "YOUR_SESSION_ID",
    "selector": ".results",
    "timeout": 10000
  }}'</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="endpoint-group">
                        <h3>📊 Data Extraction</h3>
                        
                        <div class="endpoint">
                            <div class="endpoint-header" onclick="toggleEndpoint(this)">
                                <span class="method method-post">POST</span>
                                <span class="endpoint-path">/agent/extract</span>
                                <span class="endpoint-description">Extract text or attributes from elements</span>
                            </div>
                            <div class="endpoint-body">
                                <div class="code-block">curl -X POST "{base_url}/agent/extract" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "session_id": "YOUR_SESSION_ID",
    "selector": "h1",
    "attribute": "text"
  }}'</div>
                            </div>
                        </div>
                        
                        <div class="endpoint">
                            <div class="endpoint-header" onclick="toggleEndpoint(this)">
                                <span class="method method-get">GET</span>
                                <span class="endpoint-path">/agent/screenshot</span>
                                <span class="endpoint-description">Take full-page screenshot</span>
                            </div>
                            <div class="endpoint-body">
                                <div class="code-block">curl "{base_url}/agent/screenshot?session_id=YOUR_SESSION_ID" \\
  --output screenshot.png</div>
                            </div>
                        </div>
                        
                        <div class="endpoint">
                            <div class="endpoint-header" onclick="toggleEndpoint(this)">
                                <span class="method method-get">GET</span>
                                <span class="endpoint-path">/agent/info</span>
                                <span class="endpoint-description">Get page title, URL, and metadata</span>
                            </div>
                            <div class="endpoint-body">
                                <div class="code-block">curl "{base_url}/agent/info?session_id=YOUR_SESSION_ID"</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div id="gemini" class="tab-content">
                    <div class="gemini-section">
                        <h2>🔮 Google Gemini Integration Examples</h2>
                        <p>Copy these examples to teach Gemini how to use the browser API effectively.</p>
                    </div>
                    
                    <h3>🎯 Gemini Prompt Template</h3>
                    <div class="code-block">You are a web browsing assistant. Use the Browser Agent API at {base_url} to interact with websites.

Available endpoints:
- POST /agent/visit - Start browsing a website
- POST /agent/click - Click elements  
- POST /agent/type - Fill form fields
- POST /agent/scroll - Scroll pages
- POST /agent/extract - Get text from elements
- GET /agent/screenshot - Take screenshots
- POST /agent/wait - Wait for elements to load
- GET /agent/info - Get page information
- POST /agent/close - Close browser session

Always start with /agent/visit to get a session_id, then use other endpoints with that session_id.</div>
                    
                    <h3>📝 Example 1: Google Search</h3>
                    <div class="code-block">// Gemini prompt: "Search for 'AI browser automation' on Google"

// Step 1: Visit Google
POST {base_url}/agent/visit
{{"url": "https://google.com"}}

// Step 2: Type in search box
POST {base_url}/agent/type
{{
  "session_id": "SESSION_ID",
  "selector": "input[name='q']",
  "text": "AI browser automation"
}}

// Step 3: Click search button
POST {base_url}/agent/click
{{
  "session_id": "SESSION_ID", 
  "selector": "input[name='btnK']"
}}

// Step 4: Wait for results
POST {base_url}/agent/wait
{{
  "session_id": "SESSION_ID",
  "selector": "#search"
}}

// Step 5: Extract first result title
POST {base_url}/agent/extract
{{
  "session_id": "SESSION_ID",
  "selector": "h3",
  "attribute": "text"
}}</div>
                    
                    <h3>🛒 Example 2: E-commerce Product Research</h3>
                    <div class="code-block">// Gemini prompt: "Find laptop prices on Amazon"

// 1. Visit Amazon
POST {base_url}/agent/visit
{{"url": "https://amazon.com"}}

// 2. Search for laptops
POST {base_url}/agent/type
{{
  "session_id": "SESSION_ID",
  "selector": "#twotabsearchtextbox",
  "text": "gaming laptop"
}}

// 3. Submit search
POST {base_url}/agent/click
{{"session_id": "SESSION_ID", "selector": "#nav-search-submit-button"}}

// 4. Scroll to load more products
POST {base_url}/agent/scroll
{{"session_id": "SESSION_ID", "direction": "down", "pixels": 1000}}

// 5. Extract product titles and prices
POST {base_url}/agent/extract
{{"session_id": "SESSION_ID", "selector": ".s-title-instructions-style", "attribute": "text"}}</div>
                    
                    <h3>📊 Example 3: Social Media Monitoring</h3>
                    <div class="code-block">// Gemini prompt: "Check trending topics on Twitter"

// 1. Visit Twitter/X
POST {base_url}/agent/visit
{{"url": "https://twitter.com/explore"}}

// 2. Wait for trending section to load
POST {base_url}/agent/wait
{{
  "session_id": "SESSION_ID",
  "selector": "[data-testid='trend']",
  "timeout": 10000
}}

// 3. Extract trending topics
POST {base_url}/agent/extract
{{
  "session_id": "SESSION_ID",
  "selector": "[data-testid='trend'] span",
  "attribute": "text"
}}

// 4. Take screenshot for reference
GET {base_url}/agent/screenshot?session_id=SESSION_ID</div>
                </div>
                
                <div id="workflows" class="tab-content">
                    <h2>🚀 Complete AI Workflows</h2>
                    
                    <div class="feature-grid">
                        <div class="feature-card">
                            <h3>🔍 Web Scraping</h3>
                            <p>Visit → Extract → Screenshot → Close</p>
                            <div class="code-block">1. POST /agent/visit
2. POST /agent/extract (multiple)
3. GET /agent/screenshot
4. POST /agent/close</div>
                        </div>
                        
                        <div class="feature-card">
                            <h3>📝 Form Automation</h3>
                            <p>Visit → Type → Click → Verify → Close</p>
                            <div class="code-block">1. POST /agent/visit
2. POST /agent/type (form fields)
3. POST /agent/click (submit)
4. POST /agent/wait (confirmation)
5. POST /agent/close</div>
                        </div>
                        
                        <div class="feature-card">
                            <h3>🛍️ Price Monitoring</h3>
                            <p>Visit → Search → Scroll → Extract → Compare</p>
                            <div class="code-block">1. POST /agent/visit
2. POST /agent/type (search)
3. POST /agent/scroll (load more)
4. POST /agent/extract (prices)
5. Repeat for multiple sites</div>
                        </div>
                        
                        <div class="feature-card">
                            <h3>📱 Social Monitoring</h3>
                            <p>Visit → Login → Navigate → Extract → Track</p>
                            <div class="code-block">1. POST /agent/visit
2. POST /agent/type (credentials)
3. POST /agent/click (login)
4. POST /agent/wait (dashboard)
5. POST /agent/extract (content)</div>
                        </div>
                    </div>
                    
                    <div class="live-demo">
                        <h3>🔴 Live API Status</h3>
                        <p><strong>Base URL:</strong> {base_url}</p>
                        <p><strong>Status:</strong> <span class="status-indicator"></span>Online & Ready</p>
                        <p><strong>Environment:</strong> {'Render Cloud (Production)' if is_render_environment() else 'Local Development'}</p>
                        <p><strong>Browser Mode:</strong> {'Headless (Cloud Optimized)' if get_browser_config()["headless"] else 'Headful (Debug Mode)'}</p>
                    </div>
                    
                    <h3>💡 AI Integration Tips</h3>
                    <ul style="margin-left: 2rem; color: #4b5563;">
                        <li>Always start with POST /agent/visit to get a session_id</li>
                        <li>Use POST /agent/wait for dynamic content that loads after page load</li>
                        <li>POST /agent/extract can get text, href, src, or any HTML attribute</li>
                        <li>POST /agent/scroll helps with infinite scroll pages</li>
                        <li>Screenshots are saved as PNG files with session_id.png names</li>
                        <li>Always close sessions with POST /agent/close to free resources</li>
                        <li>Use CSS selectors: #id, .class, [attribute="value"], tagname</li>
                        <li>Set appropriate timeouts for slow-loading sites</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <script>
            function showTab(tabName) {{
                document.querySelectorAll('.tab-content').forEach(tab => {{
                    tab.classList.remove('active');
                }});
                
                document.querySelectorAll('.nav-tab').forEach(tab => {{
                    tab.classList.remove('active');
                }});
                
                document.getElementById(tabName).classList.add('active');
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
        "status": "✅ Online",
        "environment": "render" if is_render_environment() else "local",
        "headless_mode": get_browser_config()["headless"],
        "ai_ready": True,
        "endpoints_active": 12,
        "base_url": "https://playwright-bqap.onrender.com"
    }

@app.post("/agent/visit")
async def visit_page(req: VisitRequest):
    try:
        browser_installed = await ensure_browser_installed()
        if not browser_installed:
            raise HTTPException(status_code=500, detail="Browser installation failed")
        
        playwright = await async_playwright().start()
        browser_config = get_browser_config()
        browser = await playwright.chromium.launch(**browser_config)
        page = await browser.new_page()
        
        # Enhanced page loading with proper waiting
        await page.goto(req.url, timeout=req.timeout)
        if req.wait_for_load:
            await page.wait_for_load_state("networkidle", timeout=req.timeout)
        
        title = await page.title()
        session_id = str(uuid.uuid4())
        sessions[session_id] = {"browser": browser, "page": page, "playwright": playwright, "url": req.url}
        
        return {
            "session_id": session_id,
            "message": f"✅ Successfully visited {req.url}",
            "title": title,
            "url": req.url,
            "headless": browser_config["headless"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Failed to visit page: {str(e)}")

@app.post("/agent/click")
async def click_element(req: ClickRequest):
    try:
        if req.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        page = sessions[req.session_id]["page"]
        
        if req.wait_for_element:
            await page.wait_for_selector(req.selector, timeout=req.timeout)
        
        await page.click(req.selector, timeout=req.timeout)
        return {"message": f"✅ Clicked {req.selector}", "session_id": req.session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Click failed: {str(e)}")

@app.post("/agent/type")
async def type_text(req: TypeRequest):
    try:
        if req.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        page = sessions[req.session_id]["page"]
        
        if req.wait_for_element:
            await page.wait_for_selector(req.selector, timeout=5000)
        
        if req.clear_first:
            await page.fill(req.selector, req.text)
        else:
            await page.type(req.selector, req.text)
        
        return {"message": f"✅ Typed '{req.text}' into {req.selector}", "session_id": req.session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Type failed: {str(e)}")

@app.post("/agent/scroll")
async def scroll_page(req: ScrollRequest):
    try:
        if req.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        page = sessions[req.session_id]["page"]
        
        if req.direction == "down":
            await page.evaluate(f"window.scrollBy(0, {req.pixels})")
        elif req.direction == "up":
            await page.evaluate(f"window.scrollBy(0, -{req.pixels})")
        elif req.direction == "right":
            await page.evaluate(f"window.scrollBy({req.pixels}, 0)")
        elif req.direction == "left":
            await page.evaluate(f"window.scrollBy(-{req.pixels}, 0)")
        
        return {"message": f"✅ Scrolled {req.direction} by {req.pixels}px", "session_id": req.session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Scroll failed: {str(e)}")

@app.post("/agent/wait")
async def wait_for_element(req: WaitRequest):
    try:
        if req.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        page = sessions[req.session_id]["page"]
        
        if req.selector:
            await page.wait_for_selector(req.selector, timeout=req.timeout)
            return {"message": f"✅ Element {req.selector} appeared", "session_id": req.session_id}
        else:
            await asyncio.sleep(req.timeout / 1000)  # Convert to seconds
            return {"message": f"✅ Waited {req.timeout}ms", "session_id": req.session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Wait failed: {str(e)}")

@app.post("/agent/extract")
async def extract_data(req: ExtractRequest):
    try:
        if req.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        page = sessions[req.session_id]["page"]
        
        if req.attribute == "text" or req.attribute is None:
            elements = await page.query_selector_all(req.selector)
            texts = []
            for element in elements:
                text = await element.text_content()
                if text and text.strip():
                    texts.append(text.strip())
            return {"data": texts, "count": len(texts), "session_id": req.session_id}
        else:
            elements = await page.query_selector_all(req.selector)
            attributes = []
            for element in elements:
                attr_value = await element.get_attribute(req.attribute)
                if attr_value:
                    attributes.append(attr_value)
            return {"data": attributes, "count": len(attributes), "session_id": req.session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Extract failed: {str(e)}")

@app.get("/agent/screenshot")
async def screenshot(session_id: str):
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        page = sessions[session_id]["page"]
        path = f"{session_id}.png"
        await page.screenshot(path=path, full_page=True)
        
        # Return the file directly
        return FileResponse(path, media_type="image/png", filename=f"screenshot_{session_id}.png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Screenshot failed: {str(e)}")

@app.get("/agent/info")
async def get_info(session_id: str):
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        page = sessions[session_id]["page"]
        title = await page.title()
        url = page.url
        
        # Get additional page info
        viewport_size = page.viewport_size
        
        return {
            "session_id": session_id,
            "title": title,
            "url": url,
            "viewport": viewport_size,
            "ready_state": await page.evaluate("document.readyState")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Info retrieval failed: {str(e)}")

@app.post("/agent/close")
async def close_browser(req: CloseRequest):
    try:
        if req.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[req.session_id]
        await session["browser"].close()
        if "playwright" in session:
            await session["playwright"].stop()
        del sessions[req.session_id]
        
        return {"message": f"✅ Session {req.session_id} closed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Close session failed: {str(e)}")

@app.get("/agent/sessions")
def list_sessions():
    active_sessions = []
    for session_id, session_data in sessions.items():
        active_sessions.append({
            "session_id": session_id,
            "url": session_data.get("url", "unknown"),
            "created": "active"
        })
    
    return {
        "active_sessions": active_sessions,
        "count": len(active_sessions),
        "status": "✅ Sessions retrieved"
    }
