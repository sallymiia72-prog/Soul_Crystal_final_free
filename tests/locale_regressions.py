"""Regression checks for language failures confirmed by mobile screenshots."""
import os,threading,json
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
source=Path(os.environ.get('TEST_HTML','index-language-fixed.html')).resolve()
class H(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(source.parent),**kwargs)
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),H)
threading.Thread(target=server.serve_forever,daemon=True).start()
checks={
 'ru':{'information':'БЛОК ИНФОРМАЦИИ','activation':'БЛОК АКТИВАЦИИ'},
 'uk':{'information':'БЛОК ІНФОРМАЦІЇ','activation':'БЛОК АКТИВАЦІЇ'},
 'en':{'information':'INFORMATION','activation':'ACTIVATION'}
}
report=[]
with sync_playwright() as p:
 browser=p.chromium.launch()
 page=browser.new_page(viewport={'width':390,'height':844})
 page.goto(f'http://127.0.0.1:{server.server_port}/{source.name}',wait_until='domcontentloaded',timeout=120000)
 for lang in ('ru','uk','en','ru'):
  page.locator(f'#soulLanguageSwitcher [data-lang="{lang}"]').click()
  page.wait_for_timeout(1200)
  labels=page.evaluate("""() => [...document.querySelectorAll('button,summary,[role="button"]')].map(e=>({text:(e.innerText||e.textContent||'').trim().replace(/\\s+/g,' '),id:e.id,visible:!!e.getClientRects().length})).filter(x=>x.visible && x.text)""")
  report.append({'language':lang,'labels':labels})
 browser.close()
server.shutdown()
out=Path('content-language-results');out.mkdir(exist_ok=True)
(out/'regressions.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
for r in report:
 lang=r['language'];labels=[x['text'] for x in r['labels']]
 print(lang,'labels',len(labels))
 for key,expected in checks[lang].items():
  matched=[t for t in labels if expected in t]
  print(' ',key,expected,'found',bool(matched))
  assert matched,f'{lang}: expected {key} label {expected!r} not found'
