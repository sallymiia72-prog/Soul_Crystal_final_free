"""Audit the committed HTML in Chromium without test CSS or JavaScript patches."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
import json, threading

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
out=Path("production-visual-results");out.mkdir(exist_ok=True)
results=[]
with sync_playwright() as p:
    browser=p.chromium.launch()
    for width in (390, 768):
        page=browser.new_page(viewport={"width":width,"height":844})
        errors=[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        page.goto(f"http://127.0.0.1:{server.server_port}/index.html",wait_until="domcontentloaded",timeout=120000)
        page.wait_for_timeout(2000)
        for lang in ("ru","uk","en","ru"):
            page.locator(f'#soulLanguageSwitcher [data-lang="{lang}"]').click()
            page.wait_for_timeout(1100)
            details=page.evaluate("""() => ({
                lang:document.documentElement.lang,
                viewport:innerWidth,
                scrollWidth:document.documentElement.scrollWidth,
                scrollY:scrollY,
                groups:[...document.querySelectorAll('.sc-main-group-info,.sc-main-group-tools')].map(e=>({
                    text:e.textContent.trim().replace(/\\s+/g,' '),
                    visible:!!e.getClientRects().length,
                    font:getComputedStyle(e).fontSize,
                    width:Math.round(e.getBoundingClientRect().width)
                }))
            })""")
            page.screenshot(path=str(out/f"actual-{width}-{lang}.png"),full_page=True)
            results.append({"width":width,"language":lang,"details":details,"errors":list(errors)})
            assert details["scrollWidth"]<=width+1,(width,lang,"horizontal overflow",details)
            expected={"ru":["БЛОК ИНФОРМАЦИИ","БЛОК АКТИВАЦИИ"],"uk":["БЛОК ІНФОРМАЦІЇ","БЛОК АКТИВАЦІЇ"],"en":["INFORMATION SECTION","ACTIVATION SECTION"]}[lang]
            grouptexts=[x["text"] for x in details["groups"]]
            assert all(any(e in t for t in grouptexts) for e in expected),(width,lang,grouptexts)
        page.close()
    browser.close()
server.shutdown()
(out/"report.json").write_text(json.dumps(results,ensure_ascii=False,indent=2))
print("PRODUCTION VISUAL AUDIT PASSED",json.dumps(results,ensure_ascii=False)[-3000:])
