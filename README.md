# Browser Agent Backend

## Features

- `/agent/visit`: Launch browser and visit a URL
- `/agent/click`: Click on elements by selector
- `/agent/type`: Fill form fields
- `/agent/screenshot`: Take a full-page screenshot
- `/agent/info`: Return page title and URL
- `/agent/close`: Close browser
- `/agent/sessions`: List active sessions
- `/health`: Liveness probe

## Run Locally

```bash
pip install -r requirements.txt
playwright install
uvicorn main:app --reload
```
