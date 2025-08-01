# Browser Agent Backend

A FastAPI-based browser automation service using Playwright. Supports both local development and cloud deployment on Render.

## 🌐 Environment Support

### Render (Production)
- ✅ **Headless mode only** - Render's container environment doesn't support GUI
- ✅ Optimized browser args for container execution
- ✅ Auto-detection of Render environment
- ❌ Visual browser mode not supported

### Local Development
- ✅ Headless and headful modes supported
- ✅ Full GUI browser window available
- ✅ Better debugging experience

## Features

- `/agent/visit`: Launch browser and visit a URL
- `/agent/click`: Click on elements by selector
- `/agent/type`: Fill form fields
- `/agent/screenshot`: Take a full-page screenshot
- `/agent/info`: Return page title and URL
- `/agent/close`: Close browser
- `/agent/sessions`: List active sessions
- `/health`: Liveness probe
- `POST /agent/visit`: Launch browser and visit a URL
- `POST /agent/click`: Click on elements by selector  
- `POST /agent/type`: Fill form fields
- `GET /agent/screenshot`: Take a full-page screenshot
- `GET /agent/info`: Return page title and URL
- `POST /agent/close`: Close browser session
- `GET /agent/sessions`: List active sessions
- `GET /health`: Health check with environment info

## 🚀 Deployment

### Render (Recommended for Production)

1. Connect your GitHub repo to Render
2. Use these build/start commands:
   ```bash
   # Build Command
   python3 -m ensurepip --upgrade && python3 -m pip install -r requirements.txt && python3 -m playwright install chromium
   
   # Start Command  
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
3. The service auto-detects Render and runs in headless mode

**Note**: Render only supports headless browser execution. Visual browser mode (`headless: false`) will not work due to container limitations.
## Run Locally

```bash
python3 -m ensurepip --upgrade && python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
uvicorn main:app --reload
```

Local development supports both headless and headful modes for easier debugging.

## 📋 API Examples

### Start a session
```bash
curl -X POST "http://localhost:8000/agent/visit" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Take a screenshot
```bash
curl "http://localhost:8000/agent/screenshot?session_id=YOUR_SESSION_ID"
```

### Check health and environment
```bash
curl "http://localhost:8000/health"
```

## 🔧 Environment Variables

The service automatically detects the deployment environment:
- `RENDER` or `RENDER_SERVICE_ID` - Indicates Render deployment
- When detected, forces headless mode with container-optimized settings

## 🐛 Troubleshooting

### On Render
- Ensure `playwright install chromium` runs during build
- Browser always runs in headless mode (this is expected)
- Check logs for missing dependencies

### Locally  
- Install system dependencies if needed: `playwright install-deps`
- Use `headless: false` for visual debugging
- Screenshots saved to project directory