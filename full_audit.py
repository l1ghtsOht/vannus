import re

with open('praxis/data.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
lines = content.split('\n')

# Find each Tool( block with start/end lines
# A Tool block starts with "    Tool(" and ends with "    )," or "    ) if False"
tool_blocks = []
i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    if stripped.startswith('Tool('):
        start = i + 1  # 1-based
        # Find name
        name_match = None
        # Find the end of this Tool block
        j = i + 1
        while j < len(lines):
            if lines[j].strip().startswith(')') or lines[j].strip().startswith(') if'):
                break
            nm = re.search(r'name="([^"]+)"', lines[j])
            if nm:
                name_match = nm.group(1)
            j += 1
        end = j + 1  # 1-based
        if name_match:
            tool_blocks.append((name_match, start, end))
        i = j + 1
    else:
        i += 1

# Group by name
from collections import defaultdict
groups = defaultdict(list)
for name, start, end in tool_blocks:
    groups[name].append((start, end))

print("=" * 70)
print("COMPREHENSIVE DUPLICATE AUDIT REPORT")
print("=" * 70)

for name in sorted(groups.keys()):
    entries = groups[name]
    if len(entries) < 2:
        continue
    print(f"\n{'─'*60}")
    print(f"DUPLICATE: \"{name}\" — {len(entries)} occurrences")
    print(f"{'─'*60}")
    for idx, (start, end) in enumerate(entries, 1):
        print(f"\n  Occurrence #{idx}: Lines {start}–{end}")
        for ln in range(start-1, end):
            if ln < len(lines):
                print(f"    {ln+1:>4}: {lines[ln]}")
    print()
