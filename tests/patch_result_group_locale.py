"""Patch the ORIGINAL language dictionaries, not a competing late translator."""
from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
needle='  window.SoulI18n={setLanguage,get language(){return active},UK,EN};'
assert s.count(needle)==1, 'Main language controller signature changed'
patch='''  Object.assign(UK, {
    "БЛОК ИНФОРМАЦИИ":"БЛОК ІНФОРМАЦІЇ",
    "БЛОК АКТИВАЦИИ":"БЛОК АКТИВАЦІЇ",
    "INFORMATION":"БЛОК ІНФОРМАЦІЇ",
    "ACTIVATION TOOLS":"БЛОК АКТИВАЦІЇ",
    "INFORMATION SECTION":"БЛОК ІНФОРМАЦІЇ",
    "ACTIVATION SECTION":"БЛОК АКТИВАЦІЇ"
  });
  Object.assign(EN, {
    "БЛОК ИНФОРМАЦИИ":"INFORMATION SECTION",
    "БЛОК АКТИВАЦИИ":"ACTIVATION SECTION",
    "БЛОК ІНФОРМАЦІЇ":"INFORMATION SECTION",
    "БЛОК АКТИВАЦІЇ":"ACTIVATION SECTION"
  });
'''
if patch not in s:s=s.replace(needle,patch+needle,1)
# Keep result headings under the same owner as the main setLanguage controller.
# The main translator uses text-node dictionaries, while later scripts may rewrite labels.
anchor='    translateTree(document.body,map);active=lang;localStorage.setItem("soul_language",lang);document.documentElement.lang=lang;'
assert s.count(anchor)==1, 'Expected single main setLanguage anchor'
replacement='''    translateTree(document.body,map);active=lang;localStorage.setItem("soul_language",lang);document.documentElement.lang=lang;
    // Canonical locale owner for result-group labels: set directly, without reverse lookup.
    const groupLabels={ru:['БЛОК ИНФОРМАЦИИ','БЛОК АКТИВАЦИИ'],uk:['БЛОК ІНФОРМАЦІЇ','БЛОК АКТИВАЦІЇ'],en:['INFORMATION SECTION','ACTIVATION SECTION']};
    const applyGroupLabels=()=>{
      for(const [i,cls] of ['sc-main-group-info','sc-main-group-tools'].entries()){
        const label=document.querySelector('.'+cls+' > span:first-child');
        if(label && label.textContent!==groupLabels[active][i])label.textContent=groupLabels[active][i];
      }
    };
    applyGroupLabels();queueMicrotask(applyGroupLabels);
    setTimeout(applyGroupLabels,200);setTimeout(applyGroupLabels,900);'''
if 'const groupLabels={ru:' not in s:s=s.replace(anchor,replacement,1)
p.write_text(s,encoding='utf-8')
print('Patched original UK/EN dictionaries for both result groups')
