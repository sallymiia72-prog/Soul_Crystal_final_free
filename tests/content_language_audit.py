"""Audit language contamination across rendered content and hidden sections."""
import asyncio,json,os,threading,re
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.async_api import async_playwright
HTML=Path(os.getenv('TEST_HTML','index-language-fixed.html')).resolve()
OUT=Path('content-language-results');OUT.mkdir(exist_ok=True)
class H(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(HTML.parent),**kw)
 def log_message(self,*a):pass
async def main():
 server=ThreadingHTTPServer(('127.0.0.1',0),H)
 threading.Thread(target=server.serve_forever,daemon=True).start()
 results=[]
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,args=['--no-sandbox'])
  page=await browser.new_page(viewport={'width':390,'height':844})
  await page.goto(f'http://127.0.0.1:{server.server_port}/{HTML.name}',wait_until='domcontentloaded',timeout=120000)
  for lang in ['ru','uk','en','ru']:
   await page.locator(f'#soulLanguageSwitcher [data-lang="{lang}"]').click()
   await page.wait_for_timeout(1300)
   items=await page.evaluate("""() => [...document.querySelectorAll('h1,h2,h3,h4,p,li,button,a,summary,label')].filter(e=>!e.closest('script,style,template')).map(e=>({text:(e.innerText||e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,400),id:e.closest('[id]')?.id||'',visible:!!e.getClientRects().length})).filter(x=>x.text.length>=8 && x.text.length<=400)""")
   # Signals requiring human review; Cyrillic in English is a strong signal, not a proof.
   visible_items=[x for x in items if x['visible']]
   suspicious=[x for x in visible_items if (lang=='en' and re.search('[А-Яа-яЁёІіЇїЄєҐґ]',x['text'])) or (lang=='ru' and re.search('[ІіЇїЄєҐґ]',x['text']))]
   results.append({'lang':lang,'total':len(items),'suspect_count':len(suspicious),'suspects':suspicious[:150],'hidden_language_versions':len(items)-len(visible_items),'mandala':[x for x in items if x['id']=='mandalaOffer'][:45]})
  await browser.close()
 server.shutdown()
 (OUT/'report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
 for x in results:print(x['lang'],'texts',x['total'],'suspect',x['suspect_count']);print('samples',[(i['id'],i['text'][:90]) for i in x['suspects'][:12]])
 # Fail only on unequivocal language leakage, not on proper names.
 if any(x['suspect_count']>0 for x in results):raise SystemExit('Potential untranslated content found; inspect report artifact')
asyncio.run(main())
