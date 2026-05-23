import json

with open('history.json', 'r', encoding='utf-8') as f:
    history = json.load(f)

print(f"Total draws in history: {len(history)}")

# Let's search for Vishu Bumper 2026-05-23
found = False
for draw in history:
    if draw.get('draw_date') == '2026-05-23':
        print("FOUND TODAY'S DRAW IN HISTORY:")
        print(json.dumps(draw, indent=2)[:1000])
        found = True
        break

if not found:
    print("Today's draw was NOT found in history!")
