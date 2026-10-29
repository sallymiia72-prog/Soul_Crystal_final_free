"""Apply two narrowly scoped V277 language JavaScript repairs to a TEST COPY."""
from pathlib import Path
source = Path("index.html")
target = source
html = source.read_text(encoding="utf-8")
replacements = [
    ('Object.assign(UK,{"Главное отличие"', 'Object.assign(window.SoulI18n.UK,{"Главное отличие"'),
    ('fixLabels();fixGuide();fixTopAndSupport()', 'fixTopAndSupport()'),
]
for before, after in replacements:
    count = html.count(before)
    if count not in (0,1):
        raise SystemExit(f"Expected exactly one match, found {count}: {before[:70]}")
    if count == 0 and after not in html: raise SystemExit('Missing original and replacement')
    html = html.replace(before, after, 1)
# Correct production mobile button sizing, not the browser test.
fixes = [
    ("font-size: 23px !important;\n    font-weight: 600 !important;", "font-size: 21px !important;\n    font-weight: 600 !important;"),
    ("st.setProperty('font-size','23px','important');", "st.setProperty('font-size','21px','important');"),
    ("font-size:23px!important;font-weight:600!important;\nborder:3px", "font-size:21px!important;font-weight:600!important;\nborder:3px"),
]
for before, after in fixes:
    if before in html:
        html = html.replace(before, after, 1)
    elif after not in html:
        raise SystemExit(f"Mobile sizing source not found: {before[:70]}")
# Scoped mobile sizing for forecast and method buttons; leave desktop untouched.
style_id = "sc-mobile-production-sizing-fix"
if style_id not in html:
    mobile_css = """<style id="sc-mobile-production-sizing-fix">
@media(max-width:600px){
html body #dayEnergyShell #dayEnergyToggle.day-energy-toggle{height:50px!important;min-height:50px!important;max-height:50px!important;margin:0!important;box-sizing:border-box!important}
html body #sc220-method-menu .sc220-method-links>button[data-sc220-panel]{font-size:21px!important;min-height:64px!important}
}
</style>"""
    html = html.replace("</head>", mobile_css+"</head>", 1)
# The forecast toggle receives an inline 62px height from legacy startup code.
# A scoped runtime correction must use the same inline !important priority.
fix_id = "sc-forecast-height-runtime-fix"
if fix_id not in html:
    runtime = """<script id="sc-forecast-height-runtime-fix">
(function(){
 function fix(){
  var el=document.getElementById('dayEnergyToggle');
  if(!el || !window.matchMedia('(max-width:600px)').matches)return;
  ['height','min-height','max-height'].forEach(function(p){el.style.setProperty(p,'50px','important')});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',fix);
 else fix();
 window.addEventListener('load',fix);
 setTimeout(fix,250);
})();
</script>"""
    if "</body>" not in html: raise SystemExit("Missing body closing tag")
    html = html.replace("</body>",runtime+"</body>",1)
target.write_text(html, encoding="utf-8")
print(f"Created {target} ({target.stat().st_size} bytes) from unmodified index.html")
