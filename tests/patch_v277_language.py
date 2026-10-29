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
target.write_text(html, encoding="utf-8")
print(f"Created {target} ({target.stat().st_size} bytes) from unmodified index.html")
