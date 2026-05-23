import re
import json

with open('scratch/today_live_text.txt', 'r', encoding='utf-8') as f:
    text = f.read()

lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]

header_regex_to_key = [
    (re.compile(r"^1st Prize", re.I), "1st_prize"),
    (re.compile(r"^Cons(olation)? Prize", re.I), "consolation_prize"),
    (re.compile(r"^2nd Prize", re.I), "2nd_prize"),
    (re.compile(r"^3rd Prize", re.I), "3rd_prize"),
    (re.compile(r"^4th Prize", re.I), "4th_prize"),
    (re.compile(r"^5th Prize", re.I), "5th_prize"),
    (re.compile(r"^6th Prize", re.I), "6th_prize"),
    (re.compile(r"^7th Prize", re.I), "7th_prize"),
    (re.compile(r"^8th Prize", re.I), "8th_prize"),
    (re.compile(r"^9th Prize", re.I), "9th_prize"),
]

parsed = {}
current_section = None
for idx, ln in enumerate(lines):
    if not ln:
        continue
    switched = False
    for rgx, key in header_regex_to_key:
        if rgx.search(ln):
            current_section = key
            if current_section not in parsed:
                parsed[current_section] = {
                    "winners": [],
                    "matched_header_line": f"{idx}: {ln}"
                }
            switched = True
            break
    if switched:
        continue
    if not current_section:
        continue
    if ln.strip() in ("**", "..."):
        continue
    tokens = re.findall(r"[A-Z]{1,3}\s*\d{4,6}|\b\d{4,6}\b", ln)
    for t in tokens:
        parsed[current_section]["winners"].append(f"{idx}: {t.strip()}")

with open('scratch/test_parse_live_output.txt', 'w', encoding='utf-8') as out_f:
    out_f.write(json.dumps(parsed, indent=2))

print("Saved live test parse trace to scratch/test_parse_live_output.txt")
