import asyncio, json, os, re, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.async_api import async_playwright

HTML = Path(os.getenv("TEST_HTML", "index.html")).resolve()
OUT = Path("language-test-results")
OUT.mkdir(exist_ok=True)
LANGS = ["ru", "uk", "en", "ru"]

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

async def main():
    results = []
    errors = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), lambda *args, **kwargs: QuietHandler(*args, directory=str(HTML.parent), **kwargs))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/{HTML.name}"
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page(viewport={"width": 390, "height": 844})
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=120000)
                await page.wait_for_timeout(2500)
                for i, lang in enumerate(LANGS):
                    step = {"step": i, "requested": lang}
                    try:
                        button = page.locator(f'#soulLanguageSwitcher [data-lang="{lang}"]')
                        if await button.count() != 1:
                            raise RuntimeError(f"Expected exactly one {lang} switcher button")
                        await button.click(timeout=12000)
                        await page.wait_for_timeout(1500)
                        actual = await page.evaluate("""() => ({
                            htmlLang: document.documentElement.lang,
                            soulLang: window.SoulI18n?.language || null,
                            active: [...document.querySelectorAll('#soulLanguageSwitcher button.active')].map(b => b.dataset.lang),
                            visibleText: document.body.innerText.slice(0, 15000),
                            pageWidth: document.documentElement.scrollWidth,
                            viewportWidth: innerWidth
                        })""")
                        text = actual.pop("visibleText")
                        step.update(actual)
                        step["cyrillic"] = len(re.findall(r"[А-Яа-яЁёІіЇїЄєҐґ]", text))
                        step["latin"] = len(re.findall(r"[A-Za-z]", text))
                        step["sample"] = text[:2000]
                        step["activeMatches"] = actual["active"] == [lang]
                        if not step["activeMatches"]:
                            step["error"] = f"Switcher active state is {actual['active']}, expected {lang}"
                        await page.screenshot(path=str(OUT / f"{i}-{lang}.png"), full_page=False)
                    except Exception as exc:
                        step["error"] = str(exc)
                    results.append(step)
            except Exception as exc:
                results.append({"fatal": str(exc)})
            finally:
                await browser.close()
    finally:
        server.shutdown()
    report = {"html": HTML.name, "steps": results, "pageErrors": errors}
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({"steps": len(results), "errors": sum("error" in x or "fatal" in x for x in results), "pageErrors": len(errors)}, ensure_ascii=False))
    if errors or any("error" in x or "fatal" in x for x in results):
        raise SystemExit(1)

asyncio.run(main())
