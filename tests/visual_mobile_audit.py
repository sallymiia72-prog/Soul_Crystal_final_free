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
html body #sc220-method-menu .sc220-method-links button, html body #sc220-method-menu .sc220-method-links button *{font-family:Arial,Helvetica,sans-serif!important;font-size:21px!important;font-weight:700!important;line-height:1.15!important;letter-spacing:0!important;text-transform:none!important;min-height:64px!important;padding:12px 15px!important}
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
assert html.count(legacy_font)==1, "Legacy font assignment changed"
html=html.replace(legacy_font, "/* font size now controlled by the scoped method-menu CSS */", 1)
print("Method button tags inspected:",inline_count)
Path("index-visual-test.html").write_text(html.replace("</body>",css+"</body>"),encoding="utf-8")
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
 page.wait_for_timeout(1500)
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
 report["buttonDetails"]=buttons.evaluate_all("(els)=>els.map(e=>({html:e.outerHTML.slice(0,450),font:getComputedStyle(e).fontSize,children:[...e.querySelectorAll('*')].slice(0,3).map(x=>({tag:x.tagName,font:getComputedStyle(x).fontSize}))}))")
 report["startupScrollY"]=page.evaluate("() => window.scrollY")
 report["viewport"]=page.evaluate("()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,scrollY:scrollY})")
 browser.close()
server.shutdown()
(out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
assert report["viewport"]["scrollWidth"]<=390,"Horizontal overflow"
assert any(x["id"]=="dayEnergyToggle" and x["measure"] and x["measure"]["height"]<=60 for x in report["checks"]),"Forecast button not compact"
assert not report["errors"],"JS errors"
assert len(report.get("buttons",[]))>=5,"Method buttons missing"
assert all(b["font"]=="21px" for b in report["buttons"][:5]),"Method fonts incorrect"
assert report["startupScrollY"]<50,"Unexpected initial scroll"
