"""Isolated browser smoke test for free Activator sections, all three languages."""
import asyncio, json, os, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.async_api import async_playwright

HTML = Path(os.getenv("TEST_HTML", "index-language-fixed.html")).resolve()
OUT = Path("activator-test-results")
OUT.mkdir(exist_ok=True)
LANGS = ["ru", "uk", "en"]
TARGETS = {
    "forecast": ("#dayEnergyToggle", "#dayEnergyDetail"),
    "activator": ("#activatorOpenButton", None),
    "geography": ("#sunPlaceToggle", "#sunPlaceDetail"),
}
class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

async def main():
    server = ThreadingHTTPServer(("127.0.0.1",0),lambda *a,**kw:Handler(*a,directory=str(HTML.parent),**kw))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    results=[]; js_errors=[]
    try:
        async with async_playwright() as p:
            browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
            page=await browser.new_page(viewport={"width":390,"height":844})
            page.on("pageerror",lambda e:js_errors.append(str(e)))
            for lang in LANGS:
                await page.goto(f"http://127.0.0.1:{server.server_port}/{HTML.name}",wait_until="domcontentloaded",timeout=120000)
                await page.wait_for_timeout(1200)
                await page.locator(f'#soulLanguageSwitcher [data-lang="{lang}"]').click()
                await page.wait_for_timeout(700)
                state=await page.evaluate("""() => ({
                    lang:document.documentElement.lang,
                    active:[...document.querySelectorAll('#soulLanguageSwitcher button.active')].map(x=>x.dataset.lang),
                    width:document.documentElement.scrollWidth,
                    viewport:innerWidth,
                    title:document.title
                })""")
                for name,(selector,detail) in TARGETS.items():
                    item={"language":lang,"section":name,"state":state}
                    try:
                        control=page.locator(selector)
                        item["exists"]=await control.count()==1
                        item["visible"]=await control.is_visible() if item["exists"] else False
                        if item["visible"]:
                            item["before"]=((await control.inner_text()) or "")[:350]
                            await control.click(timeout=8000)
                            await page.wait_for_timeout(500)
                            item["after"]=((await control.inner_text()) or "")[:350]
                            if detail:
                                item["expanded"]=await control.get_attribute("aria-expanded")
                                item["detailVisible"]=await page.locator(detail).is_visible()
                            await page.screenshot(path=str(OUT/f"{lang}-{name}.png"),full_page=False)
                        else:
                            item["note"]="Not visible in this initial state; requires further navigation"
                    except Exception as e:
                        item["error"]=str(e)[:500]
                    results.append(item)
            await browser.close()
    finally:
        server.shutdown()
    report={"html":HTML.name,"sections":results,"pageErrors":js_errors}
    (OUT/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("=== ACTIVATOR SECTIONS REPORT ===",flush=True)
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    print("=== END ACTIVATOR SECTIONS REPORT ===",flush=True)
    failures=[x for x in results if x["state"]["lang"]!=x["language"] or x["state"]["active"]!=[x["language"]] or "error" in x]
    if failures:raise SystemExit(f"{len(failures)} hard section failures")

asyncio.run(main())
