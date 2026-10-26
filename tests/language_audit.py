import asyncio, json, os, re
from pathlib import Path
from playwright.async_api import async_playwright

HTML = Path(os.getenv("TEST_HTML", "index.html")).resolve()
OUT = Path("language-test-results")
OUT.mkdir(exist_ok=True)
LANGS = ["ru", "ua", "en", "ru"]
async def main():
    results=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page=await browser.new_page(viewport={"width":390,"height":844})
        errors=[]
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        try:
            await page.goto(HTML.as_uri(), wait_until="domcontentloaded", timeout=120000)
            await page.wait_for_timeout(2500)
            for i,lang in enumerate(LANGS):
                buttons=page.locator(f'[data-lang="{lang}"]')
                if await buttons.count():
                    await buttons.first.click(timeout=8000)
                else:
                    results.append({"step":i,"lang":lang,"error":"language button not found"})
                    continue
                await page.wait_for_timeout(1200)
                actual=await page.evaluate("""() => ({
                    htmlLang:document.documentElement.lang,
                    soulLang:window.SoulI18n?.language||null,
                    text:document.body.innerText.slice(0,15000)
                })""")
                await page.screenshot(path=str(OUT/f"{i}-{lang}.png"),full_page=False)
                cyrillic=len(re.findall(r"[А-Яа-яЁёІіЇїЄєҐґ]",actual["text"]))
                latin=len(re.findall(r"[A-Za-z]",actual["text"]))
                results.append({"step":i,"requested":lang,"htmlLang":actual["htmlLang"],
                                "soulLang":actual["soulLang"],"cyrillic":cyrillic,"latin":latin,
                                "sample":actual["text"][:1500]})
        except Exception as exc:
            results.append({"fatal":str(exc)})
        await browser.close()
    (OUT/"report.json").write_text(json.dumps({"html":str(HTML),"steps":results,"pageErrors":errors},ensure_ascii=False,indent=2))
    print(json.dumps({"steps":len(results),"pageErrors":len(errors)},ensure_ascii=False))
    if errors or any("fatal" in x or "error" in x for x in results):
        raise SystemExit(1)
asyncio.run(main())
