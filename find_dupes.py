import re

with open('praxis/data.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

names = {}
for i, line in enumerate(lines, 1):
    m = re.search(r'name="([^"]+)"', line)
    if m:
        n = m.group(1)
        names.setdefault(n, []).append(i)

print("=== DUPLICATE TOOL NAMES ===")
for n, lns in sorted(names.items()):
    if len(lns) > 1:
        print(f"  {n}: lines {lns}")

# Find Notion AI dead code
print("\n=== NOTION AI / DEAD CODE ===")
for i, line in enumerate(lines, 1):
    if 'if False' in line or 'None  #' in line.strip():
        print(f"  Line {i}: {line.rstrip()}")

# Find tag casing issues
print("\n=== TAG CASING SEARCH ===")
tag_patterns = ['llm', 'seo', 'wasm', 'hitl', 'rag', 'nlp', 'api', 'ml']
for i, line in enumerate(lines, 1):
    if 'tags=' in line or 'tags =' in line:
        for pat in tag_patterns:
            # Check for lowercase version that should be uppercase
            if re.search(r'"' + pat + r'"', line, re.IGNORECASE):
                matches = re.findall(r'"([^"]*)"', line)
                relevant = [m for m in matches if m.lower() == pat.lower()]
                if relevant:
                    print(f"  Line {i}: found tag(s) {relevant} in: {line.strip()[:120]}")
