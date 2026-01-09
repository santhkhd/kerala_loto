import os
import json
import re
from datetime import datetime

NOTE_DIR = os.path.join(os.path.dirname(__file__), 'note')
MANIFEST_FILE = os.path.join(os.path.dirname(__file__), 'result_manifest.json')

def parse_result_filename(filename):
    # Example: SK-17-2025-08-29.json
    match = re.match(r'^([A-Z]{2,3})-(\d+)-(\d{4}-\d{2}-\d{2})\.json$', filename)
    if not match:
        return None
    return {
        'code': match.group(1),
        'draw_number': match.group(2),
        'date': match.group(3),
        'filename': filename
    }

def main():
    if not os.path.exists(NOTE_DIR):
        print(f"Directory {NOTE_DIR} does not exist.")
        return

    files = [f for f in os.listdir(NOTE_DIR) if f.endswith('.json')]
    manifest = []
    for f in files:
        parsed = parse_result_filename(f)
        if parsed:
            manifest.append(parsed)

    # Sort by date descending
    def get_date(x):
        try:
            return datetime.strptime(x['date'], '%Y-%m-%d')
        except:
            return datetime.min

    manifest.sort(key=get_date, reverse=True)

    # Remove duplicates
    unique_manifest = []
    seen_dates = set()
    for entry in manifest:
        if entry['date'] in seen_dates:
            continue
        seen_dates.add(entry['date'])
        unique_manifest.append(entry)

    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_manifest, f, indent=2)

    print(f"Manifest written to {MANIFEST_FILE} with {len(unique_manifest)} results.")

if __name__ == "__main__":
    main()
