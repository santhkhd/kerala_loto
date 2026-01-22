import os
import json
import requests
import re
import urllib3
from datetime import datetime
from bs4 import BeautifulSoup

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://indialotteryapi.com/wp-json/klr/v1/latest"
WEB_URL = "https://www.kllotteryresult.com/"

def get_today_date_str():
    return datetime.now().strftime("%Y-%m-%d")

# ==========================================
# 1. API METHOD
# ==========================================
def fetch_api_data():
    try:
        print(f"Checking API: {API_URL}...")
        resp = requests.get(API_URL, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"API Error: {e}")
        return None

def parse_api_data(data):
    """Converts API response to Standard Format."""
    if not data: return None
    
    draw_date = data.get("draw_date")
    draw_name = data.get("draw_name", "Unknown").upper()
    full_code = data.get("draw_code", "XX-00")
    
    # Split Code
    parts = full_code.split("-") if "-" in full_code else [full_code[:2], full_code[2:]]
    lottery_code = parts[0]
    draw_number = parts[1] if len(parts) > 1 else "00"

    # Process Prizes
    prizes_data = data.get("prizes", {})
    first_data = data.get("first", {})
    amounts_map = prizes_data.get("amounts", {})
    
    final_prizes = {}

    # 1st Prize
    winner = first_data.get("ticket", "")
    loc = first_data.get("location", "")
    if loc: winner += f" ({loc})"
    final_prizes["1st_prize"] = {
        "amount": 10000000, "label": "1st Prize",
        "winners": [winner] if winner else ["Wait"]
    }

    # Other Prizes
    std_amounts = {
        "consolation": 5000, "2nd": 3000000, "3rd": 500000,
        "4th": 5000, "5th": 2000, "6th": 1000,
        "7th": 500, "8th": 200, "9th": 100
    }
    ignore = ["amounts", "guess", "mc"]

    for api_key, val in prizes_data.items():
        if api_key in ignore: continue
        my_key = "consolation_prize" if api_key == "consolation" else f"{api_key}_prize"
        label = "Consolation Prize" if api_key == "consolation" else f"{api_key.capitalize()} Prize"
        
        winners = val if isinstance(val, list) else [val] if val else []
        
        # Amount
        amt_val = std_amounts.get(api_key, 0)
        if api_key in amounts_map:
             try: amt_val = int(re.sub(r"[^\d]", "", str(amounts_map[api_key])))
             except: pass
        
        final_prizes[my_key] = {"amount": amt_val, "label": label, "winners": winners}

    return {
        "lottery_name": draw_name,
        "draw_number": draw_number,
        "lottery_code": lottery_code,
        "draw_date": draw_date,
        "prizes": final_prizes,
        "source": "API"
    }

# ==========================================
# 2. WEB FALLBACK METHOD (kllotteryresult.com)
# ==========================================
def fetch_web_data():
    try:
        print(f"Checking Fallback Web: {WEB_URL}...")
        res = requests.get(WEB_URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Find latest result link
        link = None
        for a in soup.find_all("a", href=True):
            if re.search(r'/kerala-lottery-result-[A-Z]+-\d+', a['href']):
                link = a['href']
                if not link.startswith("http"): link = "https://www.kllotteryresult.com" + link
                break # Just get the first one (latest)
        
        if not link:
            print("Fallback: No result links found.")
            return None

        # Fetch Result Page
        print(f"Fallback: Fetching {link}...")
        p_res = requests.get(link, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        p_soup = BeautifulSoup(p_res.text, "html.parser")

        # Parse Title for Date
        title_text = ""
        h1 = p_soup.find("h1")
        if h1: title_text = h1.text.strip()
        
        m = re.search(r"(\d{2})[./-](\d{2})[./-](\d{4})", title_text)
        if not m:
            print("Fallback: Could not parse date from title.")
            return None
        
        draw_date = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        
        # Parse Name & Number
        name_m = re.search(r"([A-Za-z\s]+)\s*\(", title_text)
        draw_name = name_m.group(1).strip().upper() if name_m else "Unknown"
        
        num_m = re.search(r"\(([^)]+)\)", title_text)
        full_code = num_m.group(1) if num_m else "XX-00"
        
        parts = full_code.split("-") if "-" in full_code else [full_code[:2], full_code[2:]]
        lottery_code = parts[0]
        draw_number = parts[1] if len(parts) > 1 else "00"

        # Parse Prizes Dictionary
        prizes = {}
        prize_map = {
            "1st": "1st_prize", "Cons": "consolation_prize", "2nd": "2nd_prize",
            "3rd": "3rd_prize", "4th": "4th_prize", "5th": "5th_prize",
            "6th": "6th_prize", "7th": "7th_prize", "8th": "8th_prize",
            "9th": "9th_prize"
        }
        prize_amounts = {
            "1st_prize": 10000000, "consolation_prize": 5000, "2nd_prize": 3000000,
            "3rd_prize": 500000, "4th_prize": 5000, "5th_prize": 2000,
            "6th_prize": 1000, "7th_prize": 500, "8th_prize": 200, "9th_prize": 100
        }

        table = p_soup.find("table", class_="w-full")
        if table:
            current_key = None
            for row in table.find_all("tr"):
                th = row.find("th")
                if th:
                    label = th.get_text(strip=True)
                    for k, v in prize_map.items():
                        if k in label:
                            current_key = v
                            # Clean Label: Use standard label instead of scraped text
                            std_labels = {
                                "1st_prize": "1st Prize", "consolation_prize": "Consolation Prize",
                                "2nd_prize": "2nd Prize", "3rd_prize": "3rd Prize", "4th_prize": "4th Prize",
                                "5th_prize": "5th Prize", "6th_prize": "6th Prize", "7th_prize": "7th Prize",
                                "8th_prize": "8th Prize", "9th_prize": "9th Prize"
                            }
                            clean_label = std_labels.get(current_key, label)
                            
                            prizes[current_key] = {
                                "amount": prize_amounts.get(current_key, 0),
                                "label": clean_label,
                                "winners": []
                            }
                            break
                tds = row.find_all("td")
                if tds and current_key:
                    nums = [td.get_text(strip=True) for td in tds if td.get_text(strip=True)]
                    prizes[current_key]["winners"].extend(nums)
        
        if not prizes: return None

        return {
            "lottery_name": draw_name,
            "draw_number": draw_number,
            "lottery_code": lottery_code,
            "draw_date": draw_date,
            "prizes": prizes,
            "source": "WEB"
        }

    except Exception as e:
        print(f"Fallback Error: {e}")
        return None

# ==========================================
# 3. MAIN LOGIC
# ==========================================
def save_data(data):
    if not data: return False
    
    # Standardize Output Format
    output = {
        "lottery_name": data["lottery_name"],
        "draw_number": data["draw_number"],
        "draw_date": data["draw_date"],
        "venue": "GORKY BHAVAN NEAR BAKERY JUNCTION THIRUVANANTHAPURAM",
        "prizes": data["prizes"],
        "draw_code": f"{data['lottery_code']}-{data['draw_number']}", # Helper
        "downloadLink": "" 
    }
    
    os.makedirs('note', exist_ok=True)
    filename = f"{data['lottery_code']}-{data['draw_number']}-{data['draw_date']}.json"
    local_path = f"note/{filename}"
    
    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Saved: {local_path} (Source: {data.get('source')})")
    
    # Save Latest
    with open("note/latest.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Updated note/latest.json")
    return True

def main():
    today = get_today_date_str()
    print(f"--- Starting Update (Today: {today}) ---")
    
    # 1. Try API
    api_raw = fetch_api_data()
    api_clean = parse_api_data(api_raw)
    
    if api_clean and api_clean['draw_date'] == today:
        print("API has today's result!")
        save_data(api_clean)
    else:
        print(f"API result date ({api_clean['draw_date'] if api_clean else 'None'}) is not today.")
        
        # 2. Try Fallback
        print("Attempting Fallback Request...")
        web_clean = fetch_web_data()
        
        if web_clean and web_clean['draw_date'] == today:
            print("Fallback Web has today's result!")
            save_data(web_clean)
        else:
            print(f"Fallback Web date ({web_clean['draw_date'] if web_clean else 'None'}) is also not today.")
            print("No update performed.")
    
    # Status Update
    with open("status.json", "w") as f:
        json.dump({"last_check": today, "status": "checked"}, f)

if __name__ == "__main__":
    main()