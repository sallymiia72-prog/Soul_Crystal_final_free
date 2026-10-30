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

# Screenshot-confirmed residual locale defects, corrected at runtime after legacy renderers.
locale_fix_id = "sc-screenshot-locale-fix"
# Refresh the already-injected locale script whenever the dictionary changes.
import re
html, old_style_count = re.subn(
    r'<style id="sc-screenshot-locale-style">[\s\S]*?</style>\s*',
    '', html, count=1)
html, old_script_count = re.subn(
    r'<script id="sc-screenshot-locale-fix">[\s\S]*?</script>\s*',
    '', html, count=1)
if old_style_count != old_script_count:
    raise SystemExit('Partial locale patch found; refusing unsafe replacement')
if True:
    patch = r'''<style id="sc-screenshot-locale-style">
@media(max-width:600px){
.sc-main-group-tools button,.sc-main-group-tools [role="button"],.sc-main-group-tools .sc-activation-btn{box-sizing:border-box!important;max-width:100%!important}
.sc-main-group-tools button{white-space:normal!important;overflow-wrap:anywhere!important;word-break:normal!important;line-height:1.16!important}
}
</style>
<script id="sc-screenshot-locale-fix">
(function(){
const dict={
"Нажимай на грани Кристалла, чтобы услышать их звучание.":{
uk:"Натискай на грані Кристала, щоб почути їхнє звучання.",en:"Tap the Crystal facets to hear their sound."},
"КРИСТАЛЬНАЯ МАНДАЛА":{uk:"КРИСТАЛІЧНА МАНДАЛА",en:"CRYSTALLINE MANDALA"},
"Живая Мандала со звучанием":{uk:"Жива Мандала зі звучанням",en:"Living Mandala with Sound"},
"Полный комплект мандал":{uk:"Повний комплект мандал",en:"Complete Mandala Set"},
"ПРЕДНАЗНАЧЕНИЕ ДУШИ":{uk:"ПРИЗНАЧЕННЯ ДУШІ",en:"SOUL PURPOSE"},
"РАСКРОЙ ПРЕДНАЗНАЧЕНИЕ СВОЕЙ ДУШИ":{uk:"РОЗКРИЙ ПРИЗНАЧЕННЯ СВОЄЇ ДУШІ",en:"DISCOVER YOUR SOUL PURPOSE"},
"УЗНАЙ СВОЮ РОЛЬ В ОТНОШЕНИЯХ":{uk:"ДІЗНАЙСЯ ПРО СВОЮ РОЛЬ У СТОСУНКАХ",en:"DISCOVER YOUR ROLE IN RELATIONSHIPS"},
"ОТКРОЙ ГЕОГРАФИЮ СВОЕЙ ДУШИ":{uk:"ВІДКРИЙ ГЕОГРАФІЮ СВОЄЇ ДУШІ",en:"EXPLORE YOUR SOUL GEOGRAPHY"},
"АКТИВИРУЙ СВОЙ ЛИЧНЫЙ КРИСТАЛЛ ДУШИ":{uk:"АКТИВУЙ СВІЙ ОСОБИСТИЙ КРИСТАЛ ДУШІ",en:"ACTIVATE YOUR PERSONAL SOUL CRYSTAL"},
"МЕДИТАЦИЯ «РАЗГОВОР С ДУШОЙ»":{uk:"МЕДИТАЦІЯ «РОЗМОВА З ДУШЕЮ»",en:"MEDITATION: CONVERSATION WITH THE SOUL"},
"Введи дату рождения партнёра, чтобы узнать звёздное происхождение ваших Душ.":{uk:"Введи дату народження партнера, щоб дізнатися зоряне походження ваших Душ.",en:"Enter your partner's birth date to discover the stellar origins of your Souls."},
"И всё это можно раскрыть, имея лишь один ключ — дату рождения человека.":{uk:"І все це можна розкрити, маючи лише один ключ — дату народження людини.",en:"All of this can be revealed with just one key — a person's date of birth."},
"СВЕРНУТЬ ФУНКЦИИ":{uk:"ЗГОРНУТИ ФУНКЦІЇ",en:"COLLAPSE FEATURES"},
"ПРОВЕРИТЬ":{uk:"ПЕРЕВІРИТИ",en:"CHECK"},
"ВВЕДИ МЕСТО, КОТОРОЕ ХОЧЕШЬ ПРОВЕРИТЬ":{uk:"ВВЕДИ МІСЦЕ, ЯКЕ ХОЧЕШ ПЕРЕВІРИТИ",en:"ENTER A PLACE TO CHECK"}
};
// Screenshot-specific complete instruction fragments and labels.
Object.assign(dict,{
"ВВЕДИТЕ ДАТУ РОЖДЕНИЯ":{uk:"ВВЕДІТЬ ДАТУ НАРОДЖЕННЯ",en:"ENTER YOUR DATE OF BIRTH"},
"1. РАСЧЁТ ВИБРАЦИОННОЙ МАТРИЦЫ":{uk:"1. РОЗРАХУНОК ВІБРАЦІЙНОЇ МАТРИЦІ",en:"1. VIBRATIONAL MATRIX CALCULATION"},
"Введите дату рождения и нажмите «Рассчитать». Активатор рассчитает Вибрационную матрицу — Ваши 12 энергетических аспектов Души по сферам реализации.":{uk:"Введіть дату народження та натисніть «Розрахувати». Активатор розрахує Вібраційну матрицю — ваші 12 енергетичних аспектів Душі за сферами реалізації.",en:"Enter your date of birth and tap Calculate. The Activator will calculate your Vibrational Matrix — your Soul’s 12 energetic aspects across areas of realization."},
"Нажимая на каждую кнопку, вы получите краткое описание своей энергии в соответствующей сфере.":{uk:"Натискаючи на кожну кнопку, ви отримаєте короткий опис своєї енергії у відповідній сфері.",en:"Tap each button to see a brief description of your energy in the corresponding area."},
"Полное описание доступно по кнопке под матрицей.":{uk:"Повний опис доступний за кнопкою під матрицею.",en:"The full description is available via the button below the matrix."},
"— показывает особенности взаимодействия двух Душ и задачу их союза.":{uk:"— показує особливості взаємодії двох Душ і завдання їхнього союзу.",en:"— shows how two Souls interact and the purpose of their union."},
"— показывает основную задачу года и каждого из 12 периодов.":{uk:"— показує головне завдання року та кожного з 12 періодів.",en:"— shows the main task for the year and each of its 12 periods."},
"Я не создаю для человека новую личность. Я помогаю ему увидеть, почувствовать и проявить ту уникальность, которая уже заложена в нём.":{uk:"Я не створюю для людини нову особистість. Я допомагаю їй побачити, відчути та проявити унікальність, яка вже закладена в ній.",en:"I do not create a new personality for a person. I help them see, feel, and express the uniqueness already within them."},
"All of this can be revealed with just one key — a person’s date of birth.":{uk:"І все це можна розкрити, маючи лише один ключ — дату народження людини.",en:"All of this can be revealed with just one key — a person’s date of birth."},
"I do not create a new personality for a person. I help them see, feel and express the uniqueness that is already within them.":{uk:"Я не створюю для людини нову особистість. Я допомагаю їй побачити, відчути та проявити унікальність, яка вже закладена в ній.",en:"I do not create a new personality for a person. I help them see, feel and express the uniqueness that is already within them."},
"↑ COLLAPSE FUNCTIONS":{uk:"↑ ЗГОРНУТИ ФУНКЦІЇ",en:"↑ COLLAPSE FUNCTIONS"},
"— показывает основную задачу yeara и каждого из 12 периодов.":{uk:"— показує головне завдання року та кожного з 12 періодів.",en:"— shows the main task for the year and each of its 12 periods."}
});

// Complete text-node translations: no partial sentence replacement.
Object.assign(dict,{
"И всё это можно раскрыть, имея лишь один ключ — дату рождения человека.":{uk:"І все це можна розкрити, маючи лише один ключ — дату народження людини.",en:"All of this can be revealed with just one key — a person's date of birth."},
"Я не создаю для человека новую личность. Я помогаю ему увидеть, почувствовать и проявить ту уникальность, которая уже заложена в нём.":{uk:"Я не створюю для людини нову особистість. Я допомагаю їй побачити, відчути та проявити унікальність, яка вже закладена в ній.",en:"I do not create a new personality for a person. I help them see, feel, and express the uniqueness already within them."},
"Enter your date of birth и нажмите «Рассчитать». Активатор рассчитает Вибрационную матрицу — Ваши 12 энергетических аспектов Души по сферам реализации.":{uk:"Введіть дату народження та натисніть «Розрахувати». Активатор розрахує Вібраційну матрицю — ваші 12 енергетичних аспектів Душі за сферами реалізації.",en:"Enter your date of birth and select Calculate. The Activator calculates your Vibrational Matrix — your Soul’s 12 energetic aspects across areas of realization."}
});
// Exact screenshot-confirmed source variants and fragments in independently rendered nodes.
Object.assign(dict,{
"ВВЕДИТЕ ДАТУ РОЖДЕНИЯ":{uk:"ВВЕДІТЬ ДАТУ НАРОДЖЕННЯ",en:"ENTER YOUR DATE OF BIRTH"},
"Введіть дату народження":{uk:"Введіть дату народження",en:"Enter your date of birth"},
"Введите дату рождения":{uk:"Введіть дату народження",en:"Enter your date of birth"},
"и нажмите «Рассчитать».":{uk:"і натисніть «Розрахувати».",en:"and tap Calculate."},
"Активатор рассчитает":{uk:"Активатор розрахує",en:"The Activator will calculate"},
"Вибрационную матрицу":{uk:"Вібраційну матрицю",en:"the Vibrational Matrix"},
"Ваши 12 энергетических аспектов Души по сферам реализации.":{uk:"ваші 12 енергетичних аспектів Душі за сферами реалізації.",en:"your Soul’s 12 energetic aspects across areas of realization."},
"Нажимая на каждую кнопку, вы получите краткое описание своей энергии в соответствующей сфере.":{uk:"Натискаючи кожну кнопку, ви отримаєте короткий опис своєї енергії у відповідній сфері.",en:"Tap each button to see a brief description of your energy in the corresponding area."},
"Полное описание доступно по кнопке под матрицей.":{uk:"Повний опис доступний за кнопкою під матрицею.",en:"The full description is available via the button below the matrix."},
"УЗНАТЬ СВОЮ РОЛЬ В ОТНОШЕНИЯХ":{uk:"ДІЗНАЙСЯ ПРО СВОЮ РОЛЬ У СТОСУНКАХ",en:"DISCOVER YOUR ROLE IN RELATIONSHIPS"},
"РАСКРОЙ ПРЕДНАЗНАЧЕНИЕ СВОЕЙ ДУШИ":{uk:"РОЗКРИЙ ПРИЗНАЧЕННЯ СВОЄЇ ДУШІ",en:"DISCOVER YOUR SOUL PURPOSE"},
"УЗНАЙ ЗАДАЧУ ДУШИ НА ТЕКУЩИЙ ПЕРИОД":{uk:"ДІЗНАЙСЯ ПРО ЗАВДАННЯ ДУШІ НА ПОТОЧНИЙ ПЕРІОД",en:"DISCOVER YOUR SOUL’S TASK FOR THE CURRENT PERIOD"},
"ОТКРОЙ ГЕОГРАФИЮ СВОЕЙ ДУШИ":{uk:"ВІДКРИЙ ГЕОГРАФІЮ СВОЄЇ ДУШІ",en:"EXPLORE YOUR SOUL GEOGRAPHY"},
"— показывает особенности взаимодействия двух Душ и задачу их союза.":{uk:"— показує особливості взаємодії двох Душ і завдання їхнього союзу.",en:"— shows how two Souls interact and the purpose of their union."},
"— показывает основную задачу года и каждого из 12 периодов.":{uk:"— показує головне завдання року та кожного з 12 періодів.",en:"— shows the main task for the year and each of its 12 periods."},
"И всё это можно раскрыть, имея лишь один ключ —":{uk:"І все це можна розкрити, маючи лише один ключ —",en:"All of this can be revealed with just one key —"},
"дату народження людини.":{uk:"дату народження людини.",en:"a person’s date of birth."},
"Я не создаю для человека новую личность.":{uk:"Я не створюю для людини нову особистість.",en:"I do not create a new personality for a person."},
"Я помогаю ему увидеть, почувствовать и проявить ту уникальность, которая уже заложена в нём.":{uk:"Я допомагаю їй побачити, відчути та проявити унікальність, яка вже закладена в ній.",en:"I help them see, feel, and express the uniqueness already within them."},
"Я не создаю для человека новую личность. Я помогаю ему увидеть, почувствовать и проявить ту уникальность, которая уже заложена в нём.":{uk:"Я не створюю для людини нову особистість. Я допомагаю їй побачити, відчути та проявити унікальність, яка вже закладена в ній.",en:"I do not create a new personality for a person. I help them see, feel, and express the uniqueness already within them."},
"Твоё предназначение проявится после расчёта.":{uk:"Твоє призначення проявиться після розрахунку.",en:"Your Soul purpose will appear after calculation."},
"ПРЕДНАЗНАЧЕНИЕ ДУШИ":{uk:"ПРИЗНАЧЕННЯ ДУШІ",en:"SOUL PURPOSE"},
"In the full version, you receive an interpretation of your individual energies to understand what can guide you on the path of fulfilling your Soul purpose, together with an activation meditation for attunement with your Soul Crystal and for initiating the process of realization.":{uk:"У повній версії ви отримаєте тлумачення своїх індивідуальних енергій і медитацію активації для співналаштування з Кристалом Душі та початку реалізації призначення.",en:"In the full version, you receive an interpretation of your individual energies and an activation meditation to attune to your Soul Crystal and begin fulfilling your purpose."}
});
// Correct actual visible text, including independently rendered content and mixed-language nodes.
Object.assign(dict,{
"ВВЕДИТЕ ДАТУ РОЖДЕНИЯ":{uk:"ВВЕДІТЬ ДАТУ НАРОДЖЕННЯ",en:"ENTER YOUR DATE OF BIRTH"},
"ПРЕДНАЗНАЧЕНИЕ ДУШИ":{uk:"ПРИЗНАЧЕННЯ ДУШІ",en:"SOUL PURPOSE"},
"Твоё предназначение проявится после расчёта.":{uk:"Твоє призначення з’явиться після розрахунку.",en:"Your Soul purpose will appear after calculation."},
"УЗНАЙ СВОЮ РОЛЬ В ОТНОШЕНИЯХ":{uk:"ДІЗНАЙСЯ ПРО СВОЮ РОЛЬ У СТОСУНКАХ",en:"DISCOVER YOUR ROLE IN RELATIONSHIPS"},
"РАСКРОЙ ПРЕДНАЗНАЧЕНИЕ СВОЕЙ ДУШИ":{uk:"РОЗКРИЙ ПРИЗНАЧЕННЯ СВОЄЇ ДУШІ",en:"DISCOVER YOUR SOUL PURPOSE"},
"УЗНАЙ ЗАДАЧУ ДУШИ НА ТЕКУЩИЙ ПЕРИОД":{uk:"ДІЗНАЙСЯ ПРО ЗАВДАННЯ ДУШІ НА ПОТОЧНИЙ ПЕРІОД",en:"DISCOVER YOUR SOUL’S TASK FOR THE CURRENT PERIOD"},
"ОТКРОЙ ГЕОГРАФИЮ СВОЕЙ ДУШИ":{uk:"ВІДКРИЙ ГЕОГРАФІЮ СВОЄЇ ДУШІ",en:"EXPLORE YOUR SOUL GEOGRAPHY"},
"ВВЕДИТЕ ДАТУ РОЖДЕНИЯ":{uk:"ВВЕДІТЬ ДАТУ НАРОДЖЕННЯ",en:"ENTER YOUR DATE OF BIRTH"},
"Дату народження людини.":{uk:"дату народження людини.",en:"a person's date of birth."},
"In the full version, you receive an interpretation of your individual energies to understand what can guide you on the path of fulfilling your Soul purpose, together with an activation meditation for attunement with your Soul Crystal and for initiating the process of realization.":{uk:"У повній версії ви отримаєте тлумачення індивідуальних енергій та медитацію активації для співналаштування з Кристалом Душі й початку реалізації призначення.",en:"In the full version, you receive an interpretation of your individual energies and an activation meditation to attune to your Soul Crystal and begin fulfilling your purpose."}
});
// Restore complete locale coverage for screenshot-confirmed sections.
Object.assign(dict,{
"БЛОК ИНФОРМАЦИИ":{uk:"БЛОК ІНФОРМАЦІЇ",en:"INFORMATION SECTION"},
"БЛОК АКТИВАЦИИ":{uk:"БЛОК АКТИВАЦІЇ",en:"ACTIVATION SECTION"},
"1. РАСЧЁТ ВИБРАЦИОННОЙ МАТРИЦЫ":{uk:"1. РОЗРАХУНОК ВІБРАЦІЙНОЇ МАТРИЦІ",en:"1. VIBRATIONAL MATRIX CALCULATION"},
"Enter your date of birth и нажмите «Рассчитать». Активатор рассчитает Вибрационную матрицу — Ваши 12 энергетических аспектов Души по сферам реализации.":{uk:"Введіть дату народження та натисніть «Розрахувати». Активатор розрахує Вібраційну матрицю — ваші 12 енергетичних аспектів Душі за сферами реалізації.",en:"Enter your date of birth and select Calculate. The Activator calculates your Vibrational Matrix — your Soul’s 12 energetic aspects across areas of realization."},
"Существует три разновидности партнёрства:":{uk:"Існує три різновиди партнерства:",en:"There are three types of partnership:"},
"КАРМИЧЕСКИЕ ПАРТНЁРЫ":{uk:"КАРМІЧНІ ПАРТНЕРИ",en:"KARMIC PARTNERS"},
"РОДСТВЕННЫЕ ДУШИ":{uk:"СПОРІДНЕНІ ДУШІ",en:"KINDRED SOULS"},
"БЛИЗНЕЦОВЫЕ ПЛАМЁНА":{uk:"БЛИЗНЮКОВІ ПОЛУМ’Я",en:"TWIN FLAMES"},
"Введи дату рождения партнёра, чтобы узнать звёздное происхождение ваших Душ.":{uk:"Введи дату народження партнера, щоб дізнатися зоряне походження ваших Душ.",en:"Enter your partner’s birth date to discover your Souls’ stellar origins."},
"Дата рождения партнёра":{uk:"Дата народження партнера",en:"Partner’s date of birth"},
"ВВЕДИТЕ ДАТУ РОЖДЕНИЯ":{uk:"ВВЕДІТЬ ДАТУ НАРОДЖЕННЯ",en:"ENTER YOUR DATE OF BIRTH"}
});
// Canonical translations for screenshot-confirmed UA text remaining under EN.
Object.assign(dict,{
"МЕНТАЛЬНИЙ РІВЕНЬ":{uk:"МЕНТАЛЬНИЙ РІВЕНЬ",en:"MENTAL LEVEL"},
"ЕМОЦІЙНИЙ РІВЕНЬ":{uk:"ЕМОЦІЙНИЙ РІВЕНЬ",en:"EMOTIONAL LEVEL"},
"ФІЗИЧНИЙ РІВЕНЬ":{uk:"ФІЗИЧНИЙ РІВЕНЬ",en:"PHYSICAL LEVEL"},
"Натисніть на число, щоб відкрити інформацію про енергію.":{uk:"Натисніть на число, щоб відкрити інформацію про енергію.",en:"Tap a number to view information about its energy."},
"Натисни на грань Кристала, щоб відкрити короткий опис її енергії.":{uk:"Натисни на грань Кристала, щоб відкрити короткий опис її енергії.",en:"Tap a Crystal facet to view a brief description of its energy."},
"↓ СКАЧАТЬ ИЗОБРАЖЕНИЕ":{uk:"↓ ЗАВАНТАЖИТИ ЗОБРАЖЕННЯ",en:"↓ DOWNLOAD IMAGE"},
"СКАЧАТЬ ИЗОБРАЖЕНИЕ":{uk:"ЗАВАНТАЖИТИ ЗОБРАЖЕННЯ",en:"DOWNLOAD IMAGE"},
"ОТРИМАТИ ПОВНЕ РОЗШИФРУВАННЯ":{uk:"ОТРИМАТИ ПОВНЕ РОЗШИФРУВАННЯ",en:"GET THE FULL INTERPRETATION"},
"БЛОК ІНФОРМАЦІЇ":{uk:"БЛОК ІНФОРМАЦІЇ",en:"INFORMATION SECTION"},
"БЛОК АКТИВАЦІЇ":{uk:"БЛОК АКТИВАЦІЇ",en:"ACTIVATION SECTION"},
"РОЗКРИТИ ПРИЗНАЧЕННЯ ДУШІ":{uk:"РОЗКРИТИ ПРИЗНАЧЕННЯ ДУШІ",en:"DISCOVER YOUR SOUL PURPOSE"},
"ДІЗНАТИСЯ ПРО СВОЮ РОЛЬ У СТОСУНКАХ":{uk:"ДІЗНАТИСЯ ПРО СВОЮ РОЛЬ У СТОСУНКАХ",en:"DISCOVER YOUR ROLE IN RELATIONSHIPS"},
"ДІЗНАТИСЯ ЗАВДАННЯ ДУШІ НА ПОТОЧНИЙ ПЕРІОД":{uk:"ДІЗНАТИСЯ ЗАВДАННЯ ДУШІ НА ПОТОЧНИЙ ПЕРІОД",en:"DISCOVER YOUR SOUL’S TASK FOR THE CURRENT PERIOD"},
"ВІДКРИТИ ГЕОГРАФІЮ ДУШІ":{uk:"ВІДКРИТИ ГЕОГРАФІЮ ДУШІ",en:"EXPLORE YOUR SOUL GEOGRAPHY"},
"АКТИВУВАТИ ОСОБИСТИЙ КРИСТАЛ ДУШІ":{uk:"АКТИВУВАТИ ОСОБИСТИЙ КРИСТАЛ ДУШІ",en:"ACTIVATE YOUR PERSONAL SOUL CRYSTAL"},
"АКТИВУВАТИ ВІБРАЦІЙНИЙ КОД ДУШІ":{uk:"АКТИВУВАТИ ВІБРАЦІЙНИЙ КОД ДУШІ",en:"ACTIVATE YOUR SOUL VIBRATIONAL CODE"},
"ВСТАНОВИТИ КОНТАКТ З ВИЩИМ Я":{uk:"ВСТАНОВИТИ КОНТАКТ З ВИЩИМ Я",en:"CONNECT WITH YOUR HIGHER SELF"},
"ОТРИМАТИ КРИСТАЛІЧНУ МАНДАЛУ":{uk:"ОТРИМАТИ КРИСТАЛІЧНУ МАНДАЛУ",en:"GET YOUR CRYSTALLINE MANDALA"},
"МЕДИТАЦІЯ «РОЗМОВА З ДУШЕЮ»":{uk:"МЕДИТАЦІЯ «РОЗМОВА З ДУШЕЮ»",en:"MEDITATION: CONVERSATION WITH THE SOUL"},
"— розкриває особисту реалізацію Душі та її внесок для інших.":{uk:"— розкриває особисту реалізацію Душі та її внесок для інших.",en:"— reveals the Soul’s personal realization and its contribution to others."},
"— показує особливості взаємодії двох Душ і завдання їхнього союзу.":{uk:"— показує особливості взаємодії двох Душ і завдання їхнього союзу.",en:"— shows how two Souls interact and the purpose of their union."},
"— показує головне завдання року та кожного з 12 періодів.":{uk:"— показує головне завдання року та кожного з 12 періодів.",en:"— shows the main task for the year and each of its 12 periods."},
"— показує, як індивідуальні енергії Душі проявляються в різних місцях.":{uk:"— показує, як індивідуальні енергії Душі проявляються в різних місцях.",en:"— shows how your Soul’s individual energies manifest in different locations."},
"— відкриває особистий Кристал Душі та практику його активації.":{uk:"— відкриває особистий Кристал Душі та практику його активації.",en:"— reveals your Personal Soul Crystal and its activation practice."},
"— для прискорення реалізації призначення Душі.":{uk:"— для прискорення реалізації призначення Душі.",en:"— to accelerate the realization of your Soul purpose."},
"— активація контакту з керуючим центром Душі.":{uk:"— активація контакту з керуючим центром Душі.",en:"— activates contact with the Soul’s guiding center."},
"— персональний камертон для співналаштування з індивідуальними вібраціями Душі.":{uk:"— персональний камертон для співналаштування з індивідуальними вібраціями Душі.",en:"— a personal tuning fork for attunement to your Soul’s individual vibrations."},
"— безкоштовна медитація для внутрішнього співналаштування і контакту з Душею.":{uk:"— безкоштовна медитація для внутрішнього співналаштування і контакту з Душею.",en:"— a free meditation for inner attunement and connection with the Soul."}
});
const originals=Object.keys(dict).sort((a,b)=>b.length-a.length);
const replacements=new Map();
for(const original of originals){replacements.set(original,original);for(const v of Object.values(dict[original]))replacements.set(v,original);}
function lang(){const a=document.querySelector('#soulLanguageSwitcher [data-lang].active,#soulLanguageSwitcher [data-lang][aria-pressed="true"],#soulLanguageSwitcher [data-lang][aria-selected="true"]');const raw=a?.getAttribute('data-lang')||window.SoulI18n?.language||'ru';return raw==='ua'?'uk':raw;}
let busy=false;
function repair(){
 if(busy)return;busy=true;
 try{
 const l=lang();const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
 let n;while(n=walker.nextNode()){
  const p=n.parentElement;if(!p||p.closest('script,style,textarea,option,svg'))continue;
  const value=n.nodeValue;const trimmed=value.trim();if(!trimmed)continue;
  let original=replacements.get(trimmed);
  // Only replace a complete text node. Partial substitutions previously
  // produced mixed-language sentences and changed unrelated dynamic content.
  if(!original)continue;
  const target=l==='ru'?original:(dict[original][l]||original);
  const leading=value.match(/^\\s*/)?.[0]||'';
  const trailing=value.match(/\\s*$/)?.[0]||'';
  const next=leading+target+trailing;
  if(next!==value)n.nodeValue=next;
 }
 }finally{busy=false;}
}
let scheduled=false;
function schedule(){if(scheduled)return;scheduled=true;setTimeout(()=>{scheduled=false;repair();},60);}
const start=()=>{repair();new MutationObserver(schedule).observe(document.body,{subtree:true,childList:true,characterData:true});document.querySelector('#soulLanguageSwitcher')?.addEventListener('click',()=>{schedule();setTimeout(repair,500);},true);};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
</script>'''
    html = html.replace("</body>", patch+"</body>", 1)

target.write_text(html, encoding="utf-8")
print(f"Created {target} ({target.stat().st_size} bytes) from unmodified index.html")
