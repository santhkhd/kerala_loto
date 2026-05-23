import json

with open('result_manifest.json', 'r', encoding='utf-8') as f:
    manifest = json.load(f)

print(f"Total results in manifest: {len(manifest)}")

found = False
for entry in manifest:
    # Check if entry is a dict or string
    date_val = ""
    if isinstance(entry, dict):
        date_val = entry.get('date', '') or entry.get('draw_date', '')
        if date_val == '2026-05-23':
            print("FOUND IN MANIFEST:")
            print(json.dumps(entry, indent=2))
            found = True
    elif isinstance(entry, str):
        if '2026-05-23' in entry:
            print(f"FOUND IN MANIFEST string: {entry}")
            found = True

if not found:
    print("Today's draw not found in manifest!")
