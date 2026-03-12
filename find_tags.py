import re

with open('praxis/data.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Broader tag search - find all tag values and look for casing inconsistencies
tag_values = {}
for i, line in enumerate(lines, 1):
    if 'tags=' in line or 'tags =' in line:
        tags = re.findall(r'"([^"]+)"', line)
        for t in tags:
            key = t.lower()
            if key not in tag_values:
                tag_values[key] = []
            tag_values[key].append((t, i))

print('=== TAGS WITH MIXED CASING ===')
count = 0
for lower in sorted(tag_values.keys()):
    entries = tag_values[lower]
    casings = set(e[0] for e in entries)
    if len(casings) > 1:
        count += 1
        print(f'  Tag "{lower}":')
        for actual, ln in sorted(entries, key=lambda x: x[1]):
            print(f'    Line {ln}: "{actual}"')
if count == 0:
    print('  (none found)')

# Also specifically check for the requested patterns
print('\n=== SPECIFIC PATTERN CHECK ===')
patterns = {
    'hitl': re.compile(r'"(hitl|HITL)"', re.IGNORECASE),
    'wasm': re.compile(r'"(wasm|WASM)"', re.IGNORECASE),
    'seo': re.compile(r'"(seo|SEO)"', re.IGNORECASE),
    'llm': re.compile(r'"(llm|LLM)"', re.IGNORECASE),
    'rag': re.compile(r'"(rag|RAG)"', re.IGNORECASE),
}
for pat_name, pat in patterns.items():
    found = []
    for i, line in enumerate(lines, 1):
        m = pat.search(line)
        if m:
            found.append((i, m.group(1), line.strip()[:100]))
    if found:
        casings = set(f[1] for f in found)
        flag = " *** INCONSISTENT ***" if len(casings) > 1 else ""
        print(f'  "{pat_name}" casings found: {casings}{flag}')
        for ln, actual, ctx in found:
            print(f'    Line {ln}: "{actual}" -> {ctx}')
