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
  labels=page.evaluate("""() => [...document.querySelectorAll('button,summary,[role="button"]')].map(e=>({text:(e.textContent||'').trim().replace(/\\s+/g,' '),id:e.id,visible:!!e.getClientRects().length})).filter(x=>x.text)""")
  diagnostic=page.evaluate("""() => ({selected:document.querySelector('#soulLanguageSwitcher [data-lang].active')?.outerHTML,language:window.SoulI18n?.language,groups:[...document.querySelectorAll('.sc-main-group-info,.sc-main-group-tools')].map(e=>({html:e.outerHTML.slice(0,900),text:e.textContent.trim(),visible:!!e.getClientRects().length}))})""")
  # Fail on screenshot-confirmed untranslated phrases in rendered text.
  visible_text=page.evaluate("""() => [...document.querySelectorAll('body *')].filter(e=>e.getClientRects().length && !e.children.length && !e.closest('script,style')).map(e=>e.textContent||'').join(' ')""")
  forbidden={'uk':['ВВЕДИТЕ ДАТУ РОЖДЕНИЯ','Нажимая на каждую кнопку','Полное описание доступно','Я не создаю для человека','All of this can be revealed','ПРЕДНАЗНАЧЕНИЕ ДУШИ','Твоё предназначение проявится после расчёта','In the full version, you receive','РАСКРОЙ ПРЕДНАЗНАЧЕНИЕ','УЗНАЙ СВОЮ РОЛЬ В ОТНОШЕНИЯХ','УЗНАЙ ЗАДАЧУ ДУШИ','ОТКРОЙ ГЕОГРАФИЮ'],
             'en':['ВВЕДИТЕ ДАТУ РОЖДЕНИЯ','РАСЧЁТ ВИБРАЦИОННОЙ МАТРИЦЫ','Нажимая на каждую кнопку','Полное описание доступно','УЗНАТЬ СВОЮ РОЛЬ В ОТНОШЕНИЯХ','ПРЕДНАЗНАЧЕНИЕ ДУШИ','Твоё предназначение проявится после расчёта','РАСКРОЙ ПРЕДНАЗНАЧЕНИЕ','УЗНАЙ ЗАДАЧУ ДУШИ']} .get(lang,[])
  leaks=[x for x in forbidden if x in visible_text]
  assert not leaks, f'Screenshot-confirmed locale leakage {lang}: {leaks}'
  report.append({'language':lang,'labels':labels,'diagnostic':diagnostic})
  print('DIAGNOSTIC',lang,json.dumps(diagnostic,ensure_ascii=False),flush=True)
 browser.close()
server.shutdown()
out=Path('content-language-results');out.mkdir(exist_ok=True)
(out/'regressions.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
for r in report:
 lang=r['language'];labels=[x['text'] for x in r['labels']]
 print(lang,'labels',len(labels))
 for key,expected in checks[lang].items():
  matched=[t for t in labels if expected in t]
  print(' ',key,expected,'found',bool(matched),flush=True)
  if not matched: print('MISSING',lang,key,expected,flush=True)

missing=[(r['language'],key,expected) for r in report for key,expected in checks[r['language']].items() if not any(expected in x['text'] for x in r['labels'])]
assert not missing, f'Untranslated result headings: {missing}'
