"""Browser journey: open Activator, enter birth date, calculate in RU/UK/EN.
Isolated branch only. Never tests or triggers payments.
"""
import asyncio, json, os, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.async_api import async_playwright

HTML=Path(os.getenv("TEST_HTML","index-language-fixed.html")).resolve()
OUT=Path("activator-journey-results")
OUT.mkdir(exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

async def main():
    server=ThreadingHTTPServer(("127.0.0.1",0),lambda *a,**k:Quiet(*a,directory=str(HTML.parent),**k))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    results=[]
    try:
        async with async_playwright() as p:
            browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
            for lang in ("ru","uk","en"):
                page=await browser.new_page(viewport={"width":390,"height":844})
                errors=[]
                page.on("pageerror",lambda e:errors.append(str(e)))
                result={"language":lang}
                try:
                    await page.goto(f"http://127.0.0.1:{server.server_port}/{HTML.name}",wait_until="domcontentloaded",timeout=120000)
                    await page.wait_for_timeout(1200)
                    await page.locator(f'#soulLanguageSwitcher [data-lang="{lang}"]').click()
                    await page.wait_for_timeout(600)
                    open_button=page.locator("#activatorOpenButton")
                    result["openButtonVisible"]=await open_button.is_visible()
                    await open_button.click(timeout=12000)
                    await page.wait_for_timeout(800)
                    date=page.locator("#birthDate")
                    result["birthDateVisibleAfterOpen"]=await date.is_visible()
                    result["birthDateEnabled"]=await date.is_enabled()
                    if result["birthDateVisibleAfterOpen"] and result["birthDateEnabled"]:
                        await date.fill("21.05.1969")
                        result["enteredDate"]=await date.input_value()
                        calculate=page.locator("#calculate")
                        result["calculateVisible"]=await calculate.is_visible()
                        await calculate.click(timeout=12000)
                        await page.wait_for_timeout(1300)
                        result["validationError"]=(await page.locator("#error").inner_text())[:300]
                        result["matrixVisible"]=await page.locator("#matrixSection").is_visible()
                        result["matrixText"]=(await page.locator("#matrixSection").inner_text())[:300]
                    result["htmlLang"]=await page.locator("html").get_attribute("lang")
                    result["horizontalOverflow"]=await page.evaluate("document.documentElement.scrollWidth>innerWidth")
                    await page.screenshot(path=str(OUT/f"{lang}-journey.png"),full_page=False)
                except Exception as e:
                    result["testError"]=str(e)[:700]
                result["pageErrors"]=errors
                result["passed"]=all([
                    result.get("openButtonVisible"),result.get("birthDateVisibleAfterOpen"),
                    result.get("birthDateEnabled"),result.get("calculateVisible"),
                    result.get("enteredDate")=="21.05.1969",
                    result.get("matrixVisible"),not result.get("validationError"),
                    result.get("htmlLang")==lang,not result.get("horizontalOverflow"),
                    not errors,not result.get("testError")
                ])
                results.append(result)
                await page.close()
            await browser.close()
    finally:
        server.shutdown()
    report={"html":HTML.name,"journeys":results,"passed":all(x["passed"] for x in results)}
    (OUT/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("=== ACTIVATOR USER JOURNEY REPORT ===",flush=True)
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    print("=== END ACTIVATOR USER JOURNEY REPORT ===",flush=True)
    if not report["passed"]:raise SystemExit("Activator journey failures: inspect report.json")

asyncio.run(main())
