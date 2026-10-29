"""Patch the ORIGINAL language dictionaries, not a competing late translator."""
from pathlib import Path
p=Path('index-language-fixed.html')
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
p.write_text(s,encoding='utf-8')
print('Patched original UK/EN dictionaries for both result groups')
