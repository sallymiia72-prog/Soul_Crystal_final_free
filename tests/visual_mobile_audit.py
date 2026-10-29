from pathlib import Path
import json, os, threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

src=Path("index-language-fixed.html")
html=src.read_text(encoding="utf-8")
css="""<style id="v278-mobile-test">
@media(max-width:600px){
html body #dayEnergyShell.day-energy-shell.day-energy-outside{width:calc(100% - 42px)!important;max-width:460px!important;margin:22px auto 18px!important;position:relative!important;top:auto!important;transform:none!important}
html body #dayEnergyShell #dayEnergyToggle.day-energy-toggle{width:100%!important;height:50px!important;min-height:50px!important;max-height:50px!important;margin:0!important;padding:4px 12px!important;border-radius:24px!important;display:flex!important;align-items:center!important;justify-content:center!important;gap:6px!important;box-sizing:border-box!important}
html body #dayEnergyToggle .day-energy-left{min-width:0!important;flex:1 1 auto!important;justify-content:center!important}
html body #dayEnergyToggle .day-energy-title{font-size:13px!important;line-height:1.12!important;white-space:nowrap!important}
html body #dayEnergyToggle .day-energy-button-label,html body #dayEnergyToggle #dayEnergyButtonDate{font-size:12px!important;line-height:1.1!important;white-space:nowrap!important}
html body #dayEnergyToggle .day-energy-arrow{flex:0 0 25px!important;width:25px!important}
html body #sc220-method-menu .sc220-method-links button, html body #sc220-method-menu .sc220-method-links button *, html body button[data-sc220-panel]{font-family:Arial,Helvetica,sans-serif!important;font-size:21px!important;font-weight:700!important;line-height:1.15!important;letter-spacing:0!important;text-transform:none!important;min-height:64px!important;padding:12px 15px!important}
html body #activator-about .sc236-controls{gap:16px!important;row-gap:16px!important;margin-top:12px!important;padding-top:0!important}
}</style>
<script>try{history.scrollRestoration='manual'}catch(e){}</script>"""
# Remove only the conflicting inline font declarations on method menu buttons in the TEST copy.
import re
def clean_method_button(m):
    tag=m.group(0)
    return re.sub(r"font-size\\s*:\\s*[^;]+!important\\s*;?", "", tag, flags=re.I)
html, inline_count=re.subn(r'<button\b(?=[^>]*data-sc220-panel=)[^>]*>',clean_method_button,html,flags=re.I)
# Legacy startup JavaScript sets inline font-size with !important after DOM ready.
legacy_font = "el.style.setProperty('font-size', '1.125em', 'important');"
legacy_count = html.count(legacy_font)
print("Legacy font assignment occurrences:", legacy_count)
if legacy_count:
    html=html.replace(legacy_font, "/* font size now controlled by the scoped method-menu CSS */", 1)
print("Method button tags inspected:",inline_count)
Path("index-visual-test.html").write_text(html.replace("</head>",css+"</head>",1),encoding="utf-8")
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
 page.goto("http://127.0.0.1:8765/index-visual-test.html",wait_until="domcontentloaded",timeout=90000)
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
 # Apply the candidate production fix at the element level after legacy startup code.
 # This isolates whether the remaining 30.03px comes from the cascade or from browser scaling.
 page.evaluate("""() => {
   document.querySelectorAll('#sc220-method-menu .sc220-method-links > button[data-sc220-panel]').forEach(e => {
     e.style.setProperty('font-size','21px','important');
     e.style.setProperty('line-height','1.15','important');
     e.style.setProperty('font-weight','700','important');
     e.style.setProperty('min-height','64px','important');
   });
   const t=document.querySelector('#dayEnergyToggle');
   if(t){
     t.style.setProperty('height','50px','important');
     t.style.setProperty('min-height','50px','important');
     t.style.setProperty('max-height','50px','important');
     t.style.setProperty('margin','0','important');
   }
 }""")
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
assert all(b["font"]=="21px" for b in report["buttons"][:5]),"Method fonts incorrect; inspect FONT ROOT CAUSE"
assert report["startupScrollY"]<50,"Unexpected initial scroll"
