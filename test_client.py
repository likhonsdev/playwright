
import requests
import json
import time

# Base URL for your API
BASE_URL = "http://localhost:5000"  # Change to your deployment URL

def test_browser_agent():
    print("🧪 Testing Simple Browser Agent API")
    
    # Test 1: Visit Google
    print("\n1. Visiting Google...")
    response = requests.post(f"{BASE_URL}/visit", 
                           json={"url": "https://google.com"})
    
    if response.status_code == 200:
        data = response.json()
        session_id = data["session_id"]
        print(f"✅ Success! Session ID: {session_id}")
        print(f"   Title: {data['title']}")
    else:
        print(f"❌ Failed: {response.text}")
        return
    
    # Wait a moment
    time.sleep(2)
    
    # Test 2: Type in search box
    print("\n2. Typing in search box...")
    response = requests.post(f"{BASE_URL}/type", json={
        "session_id": session_id,
        "selector": "input[name='q']",
        "text": "hello world"
    })
    
    if response.status_code == 200:
        print("✅ Successfully typed text")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Wait a moment
    time.sleep(1)
    
    # Test 3: Take screenshot
    print("\n3. Taking screenshot...")
    response = requests.get(f"{BASE_URL}/screenshot/{session_id}")
    
    if response.status_code == 200:
        with open("test_screenshot.png", "wb") as f:
            f.write(response.content)
        print("✅ Screenshot saved as test_screenshot.png")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 4: Close session
    print("\n4. Closing session...")
    response = requests.post(f"{BASE_URL}/close", json={"session_id": session_id})
    
    if response.status_code == 200:
        print("✅ Session closed successfully")
    else:
        print(f"❌ Failed: {response.text}")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    test_browser_agent()
