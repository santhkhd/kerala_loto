import os
import json
from datetime import datetime, timedelta
import pytz

PDF_DATA_FILE = 'pdf_data.json'
TIMEZONE = 'Asia/Kolkata'

# Normal Schedule
SCHEDULE = {
    0: {'name': 'SAMRUDHI', 'code': 'SM'},     # Sunday
    1: {'name': 'BHAGYATHARA', 'code': 'BT'},   # Monday
    2: {'name': 'STHREE-SAKTHI', 'code': 'SS'}, # Tuesday
    3: {'name': 'DHANALEKSHMI', 'code': 'DL'},  # Wednesday
    4: {'name': 'KARUNYA PLUS', 'code': 'KN'},  # Thursday
    5: {'name': 'SUVARNA KERALAM', 'code': 'SK'},# Friday
    6: {'name': 'KARUNYA', 'code': 'KR'}        # Saturday
}

# Dates with no draw (Serial does not increment)
SKIPPED_DATES = [
    "26/01/2026", # Republic Day
    "12/02/2026", # Holiday
]

# Dates with multiple draws (Serial increments multiple times)
# Key: Date, Value: List of Lottery Codes
SPECIAL_DRAWS = {
    "13/02/2026": ["KN", "SK"], # Moved from 12th
    "15/01/2026": ["KN"] # DL-35 was bumper, handled separately in history but usually serialed? 
                         # Actually Feb 13 is the main known case.
}

def get_indian_date():
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz)

def parse_date_str(date_str):
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
    if not os.path.exists(file_path): return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not data: return

    latest_entry = data[0]
    last_date = parse_date_str(latest_entry['date']).replace(tzinfo=None)
    last_serial = int(latest_entry['drawserial'])

    today_naive = get_indian_date().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    
    if last_date >= today_naive:
        print(f"Data is up to date ({format_date_str(last_date)}).")
        return

    new_entries = []
    curr_date = last_date + timedelta(days=1)
    curr_serial = last_serial + 1

    while curr_date <= today_naive:
        date_str = format_date_str(curr_date)
        
        if date_str in SKIPPED_DATES:
            print(f"Skipping holiday: {date_str}")
            curr_date += timedelta(days=1)
            # DO NOT increment serial
            continue

        draw_codes = SPECIAL_DRAWS.get(date_str)
        if not draw_codes:
            day_idx = (curr_date.weekday() + 1) % 7
            info = SCHEDULE.get(day_idx)
            draw_codes = [info['code']] if info else []

        for code in draw_codes:
            # Find lottery name
            lot_name = next((v['name'] for k, v in SCHEDULE.items() if v['code'] == code), "Unknown")
            
            # Draw Number calculation
            last_num = get_latest_draw_no(data + new_entries, code)
            new_draw_no = f"{code}-{last_num + 1}"
            
            entry = {
                'lottery': lot_name,
                'draw_no': new_draw_no,
                'date': date_str,
                'drawserial': str(curr_serial),
                'url': f"https://result.keralalotteries.com/viewlotisresult.php?drawserial={curr_serial}"
            }
            new_entries.insert(0, entry)
            print(f"Generated: {date_str} - {lot_name} ({new_draw_no}) Serial: {curr_serial}")
            curr_serial += 1

        curr_date += timedelta(days=1)

    if new_entries:
        updated_data = new_entries + data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, indent=2)
        print(f"Added {len(new_entries)} entries.")

if __name__ == "__main__":
    main()
