import json

with open('note/VB-May 23, 2026-2026-05-23.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for prize_key, prize_val in data['prizes'].items():
    print(f"{prize_key}: amount={prize_val['amount']}, winners_count={len(prize_val['winners'])}")
    print(f"  First 5 winners: {prize_val['winners'][:5]}")
