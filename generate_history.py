import os
import json
import re
from datetime import datetime
from urllib.parse import quote

NOTE_DIR = os.path.join(os.path.dirname(__file__), 'note')
OUT_FILE = os.path.join(os.path.dirname(__file__), 'history.json')

def parse_json_file(file_path, file_name):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return None

    lottery = ''
    if 'lottery_name' in data:
        code_match = re.search(r'\(([A-Z]{2,3})\)', data['lottery_name'])
        lottery = code_match.group(1) if code_match else ''
    
    if not lottery and file_name:
        file_match = re.match(r'^([A-Z]{2,3})-', file_name)
        lottery = file_match.group(1) if file_match else ''

    draw = str(data.get('draw_number', '')).zfill(2)
    date = data.get('draw_date', '')
    
    prizes = []
    numbers4 = set()
    numbers6 = set()

    if 'prizes' in data and isinstance(data['prizes'], dict):
        for prize_key, prize_obj in data['prizes'].items():
            prizes.append({
                'prize_key': prize_key,
                'label': prize_obj.get('label', ''),
                'amount': prize_obj.get('amount', 0),
                'winners': prize_obj.get('winners', []) if isinstance(prize_obj.get('winners'), list) else []
            })
            
            winners = prize_obj.get('winners', [])
            if not isinstance(winners, list):
                continue

            if prize_key in ["4th_prize", "5th_prize", "6th_prize", "7th_prize", "8th_prize", "9th_prize"]:
                for w in winners:
                    m = re.search(r'\b(\d{4})\b', str(w))
                    if m:
                        numbers4.add(m.group(1))
            elif prize_key in ["1st_prize", "2nd_prize", "3rd_prize", "consolation_prize"]:
                for w in winners:
                    m = re.search(r'\b(\d{6})\b', str(w))
                    if m:
                        numbers6.add(m.group(1))

    download_link = data.get('downloadLink', '')
    github_url = f"https://raw.githubusercontent.com/santhkhd/kerala_loto/master/note/{quote(file_name)}"

    return {
        'date': date,
        'lottery': lottery,
        'draw': draw,
        'filename': file_name,
        'github_url': github_url,
        'prizes': prizes,
        'numbers4': list(numbers4),
        'numbers6': list(numbers6),
        'downloadLink': download_link
    }

def main():
    if not os.path.exists(NOTE_DIR):
        print(f"Directory {NOTE_DIR} does not exist.")
        return

    files = [f for f in os.listdir(NOTE_DIR) if f.endswith('.json')]
    history = []
    for f in files:
        result = parse_json_file(os.path.join(NOTE_DIR, f), f)
        if result and result['date'] and result['prizes']:
            history.append(result)

    def get_date(x):
        if x['date'] == "Unknown-Date":
            return datetime.min
        try:
            return datetime.strptime(x['date'], '%Y-%m-%d')
        except:
            return datetime.min

    history.sort(key=get_date, reverse=True)

    unique_history = []
    seen_dates = set()
    for entry in history:
        if entry['date'] != "Unknown-Date" and entry['date'] in seen_dates:
            continue
        seen_dates.add(entry['date'])
        unique_history.append(entry)

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_history, f, indent=2)

    print(f"Generated {OUT_FILE} with {len(unique_history)} draws.")

if __name__ == "__main__":
    main()
