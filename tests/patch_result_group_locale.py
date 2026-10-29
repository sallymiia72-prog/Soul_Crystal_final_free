"""Fix canonical result-group labels in the generated test HTML.
The same standalone patch is also applied to the downloadable client HTML.
"""
from pathlib import Path
p=Path('index-language-fixed.html')
s=p.read_text(encoding='utf-8')
marker='id="sc-result-group-locale-owner"'
if marker not in s:
 script=r"""
<script id="sc-result-group-locale-owner">
(function(){
 const labels={
  ru:['БЛОК ИНФОРМАЦИИ','БЛОК АКТИВАЦИИ'],
  ua:['БЛОК ІНФОРМАЦІЇ','БЛОК АКТИВАЦІЇ'],
  en:['INFORMATION SECTION','ACTIVATION SECTION']
 };
 let busy=false,queued=false;
 function lang(){
  const active=document.querySelector('#soulLanguageSwitcher [data-lang].active');
  let value=(active?.dataset.lang||window.SoulI18n?.language||'ru').toLowerCase();
  return value==='uk'?'ua':(labels[value]?value:'ru');
 }
 function apply(){
  if(busy)return;busy=true;
  try{
   const selected=labels[lang()];
   for(const [i,selector] of ['.sc-main-group-info','.sc-main-group-tools'].entries()){
    const btn=document.querySelector('#resultsSection > button'+selector);
    if(!btn)continue;
    const label=btn.querySelector('span:first-child');
    if(label && label.textContent!==selected[i])label.textContent=selected[i];
   }
  }finally{busy=false;}
 }
 function schedule(){if(queued)return;queued=true;setTimeout(()=>{queued=false;apply()},0);}
 function init(){
  apply();
  document.querySelector('#soulLanguageSwitcher')?.addEventListener('click',()=>{schedule();setTimeout(apply,200);setTimeout(apply,700)});
  const root=document.getElementById('resultsSection');
  if(root)new MutationObserver(schedule).observe(root,{subtree:true,childList:true,characterData:true});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
 window.scApplyResultGroupLocale=apply;
})();
</script>
"""
 s=s.replace('</body>',script+'</body>',1)
 p.write_text(s,encoding='utf-8')
print('Result group language owner installed:',marker in s)
