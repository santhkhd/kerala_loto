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

stop_keywords = [
    "how to claim", "upcoming draws", "latest lottery results", 
    "weekly schedule", "frequently asked questions", "yesterday result",
    "quick links", "disclaimer", "explore kerala lottery", "about malluz"
]

def extract_amount_from_label(label: str):
    if not label:
        return None
    cleaned = re.sub(r'[\s,\-/\\]', '', label)
    m_rs = re.search(r'(?:Rs|Rs\.|Rs:)\s*[:\.]?\s*(\d+)', cleaned, re.I)
    if m_rs:
        return int(m_rs.group(1))
    m_crore = re.search(r'(\d+(?:\.\d+)?)\s*(?:Crore|Crores|Cr)', label, re.I)
    if m_crore:
        return int(float(m_crore.group(1)) * 10000000)
    m_lakh = re.search(r'(\d+(?:\.\d+)?)\s*(?:Lakh|Lakhs|L)', label, re.I)
    if m_lakh:
        return int(float(m_lakh.group(1)) * 100000)
    m_generic = re.search(r'\b(\d{3,10})\b', cleaned)
    if m_generic:
        return int(m_generic.group(1))
    return None

parsed = {}
current_section = None
draw_year = "2026"

for idx, ln in enumerate(lines):
    if not ln:
        continue
        
    # Stop parsing completely if we hit a footer/advertisement/upcoming draws block
    should_stop = False
    for kw in stop_keywords:
        if kw in ln.lower():
            should_stop = True
            break
    if should_stop:
        print(f"Stopping at line {idx}: {ln}")
        break
        
    switched = False
    for rgx, key in header_regex_to_key:
        if rgx.search(ln):
            current_section = key
            amount = extract_amount_from_label(ln)
            
            if current_section not in parsed:
                parsed[current_section] = {
                    "amount": amount if amount is not None else 0,
                    "winners": [],
                    "matched_header_line": f"{idx}: {ln}"
                }
            else:
                # Update amount if we found a valid non-zero amount in a new header line
                if amount is not None and amount > 0:
                    parsed[current_section]["amount"] = amount
                    parsed[current_section]["matched_header_line"] += f" | {idx}: {ln}"
                    
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
        val = t.strip()
        # Ignore draw year (e.g. 2026) when it is parsed as a winner
        if val == draw_year:
            continue
        parsed[current_section]["winners"].append(val)

# De-duplicate winners for each section
for key in parsed:
    parsed[key]["winners"] = list(dict.fromkeys(parsed[key]["winners"]))

with open('scratch/test_parse_live_fixed_output.txt', 'w', encoding='utf-8') as out_f:
    out_f.write(json.dumps(parsed, indent=2))

print("Saved fixed live test parse trace to scratch/test_parse_live_fixed_output.txt")
