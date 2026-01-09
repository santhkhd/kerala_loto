import os
import json
from datetime import datetime, timedelta
import pytz

PDF_DATA_FILE = 'pdf_data.json'
TIMEZONE = 'Asia/Kolkata'

SCHEDULE = {
    0: {'name': 'SAMRUDHI', 'code': 'SM'},     # Sunday
    1: {'name': 'BHAGYATHARA', 'code': 'BT'},   # Monday
    2: {'name': 'STHREE-SAKTHI', 'code': 'SS'}, # Tuesday
    3: {'name': 'DHANALEKSHMI', 'code': 'DL'},  # Wednesday
    4: {'name': 'KARUNYA PLUS', 'code': 'KN'},  # Thursday
    5: {'name': 'SUVARNA KERALAM', 'code': 'SK'},# Friday
    6: {'name': 'KARUNYA', 'code': 'KR'}        # Saturday
}

def get_indian_date():
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz)

def parse_date_str(date_str):
    # dd/mm/yyyy
    return datetime.strptime(date_str, '%d/%m/%Y')

def format_date_str(date_obj):
    return date_obj.strftime('%d/%m/%Y')

def get_latest_draw_no(data, code):
    max_num = 0
    for item in data:
        if item['draw_no'].startswith(code + '-'):
            try:
                num = int(item['draw_no'].split('-')[1])
                if num > max_num:
                    max_num = num
            except:
                pass
    return max_num

def main():
    file_path = os.path.join(os.path.dirname(__file__), PDF_DATA_FILE)

    if not os.path.exists(file_path):
        print("No existing data found.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not data:
        print("Empty data file.")
        return

    latest_entry = data[0]
    last_date = parse_date_str(latest_entry['date'])
    last_serial = int(latest_entry['drawserial'])

    today = get_indian_date().replace(hour=0, minute=0, second=0, microsecond=0)
    last_date = last_date.replace(tzinfo=None) # Make it naive for comparison if needed, or better use timezone everywhere
    # Ensure both are comparable
    today_naive = today.replace(tzinfo=None)
    
    if last_date >= today_naive:
        print(f"Data is up to date ({format_date_str(last_date)}). No new PDFs to generate.")
        return

    new_entries = []
    curr_date = last_date + timedelta(days=1)
    curr_serial = last_serial + 1

    while curr_date <= today_naive:
        day_idx = curr_date.weekday() # Monday=0, Sunday=6 in Python
        # Adjust index to match JS/My Schedule if necessary. 
        # My SCHEDULE mapping: 0=Sunday, 1=Monday... 6=Saturday.
        # Python weekday(): 0=Monday, 6=Sunday.
        # Conversion: (day_idx + 1) % 7
        js_day_idx = (day_idx + 1) % 7
        info = SCHEDULE.get(js_day_idx)

        if info:
            # Check existing data
            last_num = get_latest_draw_no(data, info['code'])
            # Check newly added ones
            for e in new_entries:
                if e['draw_no'].startswith(info['code'] + '-'):
                    try:
                        num = int(e['draw_no'].split('-')[1])
                        if num > last_num:
                            last_num = num
                    except:
                        pass

            new_draw_no = f"{info['code']}-{last_num + 1}"
            date_str = format_date_str(curr_date)

            entry = {
                'lottery': info['name'],
                'draw_no': new_draw_no,
                'date': date_str,
                'drawserial': str(curr_serial),
                'url': f"https://result.keralalotteries.com/viewlotisresult.php?drawserial={curr_serial}"
            }

            new_entries.insert(0, entry) # Add to front
            print(f"Generated: {entry['date']} - {entry['lottery']} ({entry['draw_no']})")

        curr_date += timedelta(days=1)
        curr_serial += 1

    if new_entries:
        updated_data = new_entries + data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, indent=2)
        print(f"Added {len(new_entries)} new entries to {PDF_DATA_FILE}")
    else:
        print("No valid lottery days found in the gap.")

if __name__ == "__main__":
    main()
