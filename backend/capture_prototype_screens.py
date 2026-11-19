import asyncio
import json
import time
import subprocess
import urllib.request
import base64
from pathlib import Path
import websockets

SCREEN_DIR = Path("backend/captured_screens")
SCREEN_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR = Path("chrome_capture_profile")

async def send_cdp(ws, method, params=None, msg_id=1):
    msg = {"id": msg_id, "method": method}
    if params:
        msg["params"] = params
    await ws.send(json.dumps(msg))
    while True:
        res = json.loads(await ws.recv())
        if res.get("id") == msg_id:
            return res

async def evaluate_js(ws, script, msg_id=1):
    return await send_cdp(ws, "Runtime.evaluate", {"expression": script, "awaitPromise": True}, msg_id)

async def take_screenshot(ws, filename, msg_id=1):
    res = await send_cdp(ws, "Page.captureScreenshot", {"format": "png"}, msg_id)
    b64_data = res["result"]["data"]
    img_bytes = base64.b64decode(b64_data)
    filepath = SCREEN_DIR / filename
    filepath.write_bytes(img_bytes)
    print(f"Captured {filename} ({len(img_bytes)} bytes)")
    return filepath

async def main():
    print("Launching Chrome in headless mode with CDP on port 9222...")
    chrome_proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        "--remote-debugging-port=9222",
        f"--user-data-dir={PROFILE_DIR.resolve()}",
        "--window-size=1280,720",
        "--disable-gpu",
        "--hide-scrollbars",
        "about:blank"
    ])
    
    time.sleep(2)
    
    try:
        tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json/list").read())
        ws_url = tabs[0]["webSocketDebuggerUrl"]
        print(f"Connecting to CDP WebSocket: {ws_url}")
        
        async with websockets.connect(ws_url, max_size=50_000_000) as ws:
            # 1. Navigate to Login Page
            await send_cdp(ws, "Page.enable", {}, 10)
            await send_cdp(ws, "Page.navigate", {"url": "http://127.0.0.1:8000/"}, 11)
            await asyncio.sleep(2)
            
            # Fill Demo Farmer
            await evaluate_js(ws, "document.getElementById('btnFillFarmer').click()", 12)
            await asyncio.sleep(1)
            await take_screenshot(ws, "01_login.png", 13)
            
            # Submit Login Form
            await evaluate_js(ws, "document.getElementById('loginForm').dispatchEvent(new Event('submit', { cancelable: true }))", 14)
            await asyncio.sleep(3)
            
            # 2. Add Produce Tab
            await evaluate_js(ws, "document.querySelector('a[data-tab=\"tabAdd\"]').click()", 20)
            await asyncio.sleep(1.5)
            await evaluate_js(ws, "document.getElementById('batchCrop').value = 'mango'", 21)
            await evaluate_js(ws, "document.getElementById('batchQuantity').value = '500'", 22)
            await evaluate_js(ws, "document.getElementById('batchAmbientTemp').value = '32.0'", 23)
            await asyncio.sleep(1)
            await take_screenshot(ws, "02_add_produce.png", 24)
            
            # 3. SRI & Batches Tab
            await evaluate_js(ws, "document.querySelector('a[data-tab=\"tabBatches\"]').click()", 30)
            await asyncio.sleep(2.5)
            await take_screenshot(ws, "03_sri_batches.png", 31)
            
            # 4. Cooling Map Tab
            await evaluate_js(ws, "document.querySelector('a[data-tab=\"tabCoolingMap\"]').click()", 40)
            await asyncio.sleep(2.5)
            await take_screenshot(ws, "04_cooling_map.png", 41)
            
            # 5. Cooling Matches Tab
            await evaluate_js(ws, "document.querySelector('a[data-tab=\"tabMatching\"]').click()", 50)
            await asyncio.sleep(2.5)
            await take_screenshot(ws, "05_matching.png", 51)
            
            # 6. Bookings Tab
            await evaluate_js(ws, "document.querySelector('a[data-tab=\"tabBookings\"]').click()", 60)
            await asyncio.sleep(2.5)
            await take_screenshot(ws, "06_bookings.png", 61)
            
            print("All prototype screens captured successfully!")
            
    finally:
        chrome_proc.terminate()
        chrome_proc.wait()

if __name__ == "__main__":
    asyncio.run(main())
