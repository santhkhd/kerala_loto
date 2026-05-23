import json

with open('history.json', 'r', encoding='utf-8') as f:
    history = json.load(f)

# Let's search for entries on 2026-05-23
found = False
for draw in history:
    if draw.get('date') == '2026-05-23':
        print("FOUND ENTRY ON 2026-05-23:")
        print(json.dumps(draw, indent=2))
        found = True

if not found:
    print("No entries on 2026-05-23 found.")
