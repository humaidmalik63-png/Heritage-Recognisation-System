import asyncio
import websockets
import json
import subprocess
import tempfile
import os
import time
import base64
import urllib.request
import shutil

async def capture_all():
    port = 5175
    url = f"http://localhost:{port}/"

    output_dir = os.path.abspath(os.path.join("frontend", "screenshots-phase10-3"))
    os.makedirs(output_dir, exist_ok=True)
    artifacts_dir = r"C:\Users\humai\.gemini\antigravity\brain\65f04f8f-d136-410f-b3f3-0096c601b0ae"

    user_data = tempfile.mkdtemp()
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    proc = subprocess.Popen([
        chrome_path,
        "--headless=new",
        "--disable-gpu",
        f"--user-data-dir={user_data}",
        "--remote-debugging-port=9455",
        "about:blank"
    ])

    await asyncio.sleep(2)

    try:
        tabs = json.loads(urllib.request.urlopen("http://localhost:9455/json").read())
        ws_url = None
        for t in tabs:
            if t.get("type") == "page":
                ws_url = t.get("webSocketDebuggerUrl")
                break
        if not ws_url:
            ws_url = tabs[0]["webSocketDebuggerUrl"]

        async with websockets.connect(ws_url, max_size=25000000) as ws:
            cmd_counter = 1
            async def call_cmd(method, params=None):
                nonlocal cmd_counter
                cmd_id = cmd_counter
                cmd_counter += 1
                msg = {"id": cmd_id, "method": method}
                if params:
                    msg["params"] = params
                await ws.send(json.dumps(msg))
                while True:
                    r = await ws.recv()
                    res = json.loads(r)
                    if res.get("id") == cmd_id:
                        return res

            await call_cmd("Page.enable")
            await call_cmd("DOM.enable")
            await call_cmd("Runtime.enable")

            # Navigate
            print(f"Navigating to {url}...")
            await call_cmd("Page.navigate", {"url": url})
            await asyncio.sleep(3)

            # 1. Capture Desktop Viewports
            desktop_viewports = [
                (1920, 1080, "desktop_1920x1080.png"),
                (1440, 900, "desktop_1440x900.png"),
                (1280, 800, "desktop_1280x800.png"),
            ]

            for width, height, fname in desktop_viewports:
                await call_cmd("Emulation.setDeviceMetricsOverride", {
                    "width": width,
                    "height": height,
                    "deviceScaleFactor": 1,
                    "mobile": False
                })
                await asyncio.sleep(1)
                shot = await call_cmd("Page.captureScreenshot", {"format": "png"})
                data = base64.b64decode(shot["result"]["data"])
                out_path = os.path.join(output_dir, fname)
                with open(out_path, "wb") as f:
                    f.write(data)
                # Copy to artifacts
                shutil.copy(out_path, os.path.join(artifacts_dir, fname))
                print(f"Captured {fname} ({width}x{height}) - {len(data)} bytes")

            # 2. Capture Mobile Viewports
            mobile_viewports = [
                (430, 932, "mobile_430x932.png"),
                (390, 844, "mobile_390x844.png"),
                (360, 800, "mobile_360x800.png"),
            ]

            for width, height, fname in mobile_viewports:
                await call_cmd("Emulation.setDeviceMetricsOverride", {
                    "width": width,
                    "height": height,
                    "deviceScaleFactor": 2,
                    "mobile": True
                })
                await asyncio.sleep(1)
                shot = await call_cmd("Page.captureScreenshot", {"format": "png"})
                data = base64.b64decode(shot["result"]["data"])
                out_path = os.path.join(output_dir, fname)
                with open(out_path, "wb") as f:
                    f.write(data)
                shutil.copy(out_path, os.path.join(artifacts_dir, fname))
                print(f"Captured {fname} ({width}x{height}) - {len(data)} bytes")

            # 3. Mobile Tab Switching: Switch to Archive Tab
            print("Switching mobile tab to Archive...")
            await call_cmd("Runtime.evaluate", {
                "expression": """
                const buttons = Array.from(document.querySelectorAll('nav button'));
                const archiveBtn = buttons.find(b => b.textContent.includes('Archive'));
                if (archiveBtn) archiveBtn.click();
                """
            })
            await asyncio.sleep(1.5)
            shot = await call_cmd("Page.captureScreenshot", {"format": "png"})
            data = base64.b64decode(shot["result"]["data"])
            out_path = os.path.join(output_dir, "mobile_tab_archive_390x844.png")
            with open(out_path, "wb") as f:
                f.write(data)
            shutil.copy(out_path, os.path.join(artifacts_dir, "mobile_tab_archive_390x844.png"))
            print(f"Captured mobile_tab_archive_390x844.png - {len(data)} bytes")

            # 4. Mobile Monument Details Sheet: Open Petra Dossier
            print("Opening Petra Dossier bottom sheet on mobile...")
            await call_cmd("Runtime.evaluate", {
                "expression": """
                const dossierButtons = Array.from(document.querySelectorAll('button'));
                const dossierBtn = dossierButtons.find(b => b.textContent.trim() === 'Dossier');
                if (dossierBtn) dossierBtn.click();
                """
            })
            await asyncio.sleep(1.5)
            shot = await call_cmd("Page.captureScreenshot", {"format": "png"})
            data = base64.b64decode(shot["result"]["data"])
            out_path = os.path.join(output_dir, "mobile_dossier_modal_390x844.png")
            with open(out_path, "wb") as f:
                f.write(data)
            shutil.copy(out_path, os.path.join(artifacts_dir, "mobile_dossier_modal_390x844.png"))
            print(f"Captured mobile_dossier_modal_390x844.png - {len(data)} bytes")

            # Close modal
            await call_cmd("Runtime.evaluate", {
                "expression": """
                const dismissBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Dismiss');
                if (dismissBtn) dismissBtn.click();
                """
            })
            await asyncio.sleep(1)

            # 5. Mobile Tab Switching: Switch to Recognise Tab
            print("Switching mobile tab to Recognise...")
            await call_cmd("Runtime.evaluate", {
                "expression": """
                const buttons = Array.from(document.querySelectorAll('nav button'));
                const scanBtn = buttons.find(b => b.textContent.includes('Scan') || b.textContent.includes('Recognise'));
                if (scanBtn) scanBtn.click();
                """
            })
            await asyncio.sleep(1.5)
            shot = await call_cmd("Page.captureScreenshot", {"format": "png"})
            data = base64.b64decode(shot["result"]["data"])
            out_path = os.path.join(output_dir, "mobile_tab_recognise_390x844.png")
            with open(out_path, "wb") as f:
                f.write(data)
            shutil.copy(out_path, os.path.join(artifacts_dir, "mobile_tab_recognise_390x844.png"))
            print(f"Captured mobile_tab_recognise_390x844.png - {len(data)} bytes")

            # 6. Mobile Tab Switching: Switch to Log / History Tab
            print("Switching mobile tab to Log / History...")
            await call_cmd("Runtime.evaluate", {
                "expression": """
                const buttons = Array.from(document.querySelectorAll('nav button'));
                const logBtn = buttons.find(b => b.textContent.includes('Log'));
                if (logBtn) logBtn.click();
                """
            })
            await asyncio.sleep(1.5)
            shot = await call_cmd("Page.captureScreenshot", {"format": "png"})
            data = base64.b64decode(shot["result"]["data"])
            out_path = os.path.join(output_dir, "mobile_tab_log_390x844.png")
            with open(out_path, "wb") as f:
                f.write(data)
            shutil.copy(out_path, os.path.join(artifacts_dir, "mobile_tab_log_390x844.png"))
            print(f"Captured mobile_tab_log_390x844.png - {len(data)} bytes")

            # 7. Mobile Tab Switching: Switch to About Tab
            print("Switching mobile tab to About...")
            await call_cmd("Runtime.evaluate", {
                "expression": """
                const buttons = Array.from(document.querySelectorAll('nav button'));
                const aboutBtn = buttons.find(b => b.textContent.includes('About'));
                if (aboutBtn) aboutBtn.click();
                """
            })
            await asyncio.sleep(1.5)
            shot = await call_cmd("Page.captureScreenshot", {"format": "png"})
            data = base64.b64decode(shot["result"]["data"])
            out_path = os.path.join(output_dir, "mobile_tab_about_390x844.png")
            with open(out_path, "wb") as f:
                f.write(data)
            shutil.copy(out_path, os.path.join(artifacts_dir, "mobile_tab_about_390x844.png"))
            print(f"Captured mobile_tab_about_390x844.png - {len(data)} bytes")

            print("\nAll Phase 10.3 screenshots captured successfully!")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except:
            proc.kill()
        shutil.rmtree(user_data, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(capture_all())

