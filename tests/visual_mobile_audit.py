from pathlib import Path
import json, os, threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

src=Path("index.html")
html=src.read_text(encoding="utf-8")
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args): pass
server=ThreadingHTTPServer(("127.0.0.1",8765),Quiet)
threading.Thread(target=server.serve_forever,daemon=True).start()
out=Path("visual-audit-results");out.mkdir(exist_ok=True)
report={"checks":[],"errors":[]}
with sync_playwright() as p:
 browser=p.chromium.launch()
 page=browser.new_page(viewport={"width":390,"height":844},device_scale_factor=1)
 page.on("pageerror",lambda e:report["errors"].append(str(e)))
 page.goto("http://127.0.0.1:8765/index.html",wait_until="domcontentloaded",timeout=90000)
 # Record scroll changes and their JavaScript callers before any audit interaction.
 page.add_init_script("""(() => {
   window.__scrollTrace=[];
   const save=(kind,extra={})=>window.__scrollTrace.push({kind,at:Math.round(performance.now()),y:scrollY,hash:location.hash,active:document.activeElement?.id||document.activeElement?.tagName,...extra});
   addEventListener('scroll',()=>save('scroll'),{passive:true});
   for(const method of ['scrollTo','scrollBy']){
     const original=window[method].bind(window);
     window[method]=function(...args){save(method,{args:String(args),stack:new Error().stack?.slice(0,600)});return original(...args)};
   }
   addEventListener('DOMContentLoaded',()=>save('DOMContentLoaded'));
   addEventListener('load',()=>save('load'));
 })()""")
 page.wait_for_timeout(1500)
 report["scrollTrace"]=page.evaluate("() => window.__scrollTrace||[]")
 print("SCROLL TRACE",json.dumps(report["scrollTrace"],ensure_ascii=False),flush=True)
 report["startupScrollY"]=page.evaluate("() => window.scrollY")
 report["startupScrollDiagnostics"]=page.evaluate("""() => ({hash:location.hash,activeElement:document.activeElement?.outerHTML.slice(0,300),scrollRestoration:history.scrollRestoration,scrollingElement:document.scrollingElement?.tagName,scrollingElementTop:document.scrollingElement?.scrollTop,bodyTop:document.body.scrollTop,topElements:[...document.querySelectorAll("body *")].filter(e=>{const r=e.getBoundingClientRect();return r.top>=-10&&r.top<=30&&r.height>20}).slice(0,8).map(e=>({tag:e.tagName,id:e.id,cls:String(e.className).slice(0,100)}))})""")
 print("STARTUP SCROLL DIAGNOSTIC",json.dumps(report["startupScrollDiagnostics"],ensure_ascii=False),flush=True)
 page.screenshot(path=str(out/"initial.png"))
 for id in ["dayEnergyShell","dayEnergyToggle","sc220-method-menu"]:
  e=page.locator("#"+id)
  report["checks"].append({"id":id,"count":e.count(),"measure":e.first.evaluate("(e)=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {width:r.width,height:r.height,top:r.top,font:s.fontSize,marginTop:s.marginTop}}") if e.count() else None})
 menu=page.locator("#sc220-method-menu")
 if menu.count():
  try: menu.locator("summary").click(timeout=3000)
  except Exception: pass
  buttons=page.locator("#sc220-method-menu .sc220-method-links > button")
  report["buttons"]=buttons.evaluate_all("(els)=>els.map(e=>({text:e.innerText,font:getComputedStyle(e).fontSize,height:e.getBoundingClientRect().height}))")
  page.screenshot(path=str(out/"method.png"))
 report["cssEnvironment"]=page.evaluate("()=>({viewport:innerWidth,media600:matchMedia('(max-width:600px)').matches,styles:[...document.querySelectorAll('#v278-mobile-test')].map(x=>({sheet:!!x.sheet,media:x.sheet?.cssRules?.[0]?.conditionText,ruleCount:x.sheet?.cssRules?.length})),buttonCount:document.querySelectorAll('button[data-sc220-panel]').length})")
 report["cssRuleLoaded"]=page.evaluate("()=>!!document.querySelector('#v278-mobile-test')")
 report["selectorDiagnostics"]=buttons.evaluate_all("(els)=>els.map(e=>({matches:e.matches('html body #sc220-method-menu .sc220-method-links button'),parent:e.parentElement?.outerHTML.slice(0,180),ancestor:e.closest('#sc220-method-menu')?.id,computed:getComputedStyle(e).fontSize}))")
 report["buttonDetails"]=buttons.evaluate_all("(els)=>els.map(e=>({html:e.outerHTML.slice(0,450),font:getComputedStyle(e).fontSize,children:[...e.querySelectorAll('*')].slice(0,3).map(x=>({tag:x.tagName,font:getComputedStyle(x).fontSize}))}))")
 report["fontRootCause"]=page.evaluate("""() => {
 const e=document.querySelector('button[data-sc220-panel="universe-architecture"]');
 if(!e)return {missing:true};
 const r=e.getBoundingClientRect(),cs=getComputedStyle(e);
 const styles=[...document.querySelectorAll('style')];
 return {font:cs.fontSize,styleFont:e.style.getPropertyValue('font-size'),stylePriority:e.style.getPropertyPriority('font-size'),selectorMatches:e.matches('html body button[data-sc220-panel]'),viewportMatch:matchMedia('(max-width:600px)').matches,styleCount:styles.length,auditStyles:styles.filter(x=>x.id==='v278-mobile-test').map(x=>({length:x.textContent.length,sheet:!!x.sheet,cssRules:x.sheet?.cssRules.length})),rect:{width:r.width,height:r.height},ancestor:e.parentElement?.className};
 }""")
 print("FONT ROOT CAUSE",json.dumps(report["fontRootCause"],ensure_ascii=False),flush=True)
 report["viewport"]=page.evaluate("()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,scrollY:scrollY})")
 browser.close()
server.shutdown()
(out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
assert report["viewport"]["scrollWidth"]<=390,"Horizontal overflow"
assert any(x["id"]=="dayEnergyToggle" and x["measure"] and abs(x["measure"]["height"]-50)<0.6 for x in report["checks"]),"Forecast button is not 50px"
assert not report["errors"],"JS errors"
assert len(report.get("buttons",[]))>=5,"Method buttons missing"
assert all(b["font"]=="21px" for b in report["buttons"][:5]),"Actual method button fonts differ from 21px"
assert report["startupScrollY"]<50,"Unexpected initial scroll"
