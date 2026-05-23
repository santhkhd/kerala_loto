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

# Mappings
prize_map = {
    "1st": "1st_prize", "1st Prize": "1st_prize",
    "Cons": "consolation_prize", "Cons Prize": "consolation_prize",
    "Cons Prize-Rs": "consolation_prize", "Consolation": "consolation_prize",
    "Consolation Prize": "consolation_prize", "2nd": "2nd_prize", "2nd Prize": "2nd_prize",
    "3rd": "3rd_prize", "3rd Prize": "3rd_prize", "4th": "4th_prize", "4th Prize": "4th_prize",
    "5th": "5th_prize", "5th Prize": "5th_prize", "6th": "6th_prize", "6th Prize": "6th_prize",
    "7th": "7th_prize", "7th Prize": "7th_prize", "8th": "8th_prize", "8th Prize": "8th_prize",
    "9th": "9th_prize", "9th Prize": "9th_prize"
}
prize_amounts = {
    "1st_prize": 10000000, "consolation_prize": 5000, "2nd_prize": 3000000,
    "3rd_prize": 500000, "4th_prize": 5000, "5th_prize": 2000,
    "6th_prize": 1000, "7th_prize": 500, "8th_prize": 200, "9th_prize": 100
}
standard_labels = {
    "1st_prize": "1st Prize", "consolation_prize": "Consolation Prize",
    "2nd_prize": "2nd Prize", "3rd_prize": "3rd Prize", "4th_prize": "4th Prize",
    "5th_prize": "5th Prize", "6th_prize": "6th Prize", "7th_prize": "7th Prize",
    "8th_prize": "8th Prize", "9th_prize": "9th Prize"
}

def extract_amount_from_label(label: str) -> Optional[int]:
    """Dynamically extracts the numeric prize amount from the label or text row."""
    if not label:
        return None
    # Clean label to remove spaces, commas, and hyphens for numeric checks
    cleaned = re.sub(r'[\s,\-/\\]', '', label)
    
    # 1. Match standard patterns like Rs.120000000 or Rs120000000 or Rs:120000000
    m_rs = re.search(r'(?:Rs|Rs\.|Rs:)\s*[:\.]?\s*(\d+)', cleaned, re.I)
    if m_rs:
        try:
            return int(m_rs.group(1))
        except ValueError:
            pass
            
    # 2. Textual matches like "12 Crore" or "10 Lakh" or "1 Crore"
    m_crore = re.search(r'(\d+(?:\.\d+)?)\s*(?:Crore|Crores|Cr)', label, re.I)
    if m_crore:
        try:
            return int(float(m_crore.group(1)) * 10000000)
        except ValueError:
            pass
            
    m_lakh = re.search(r'(\d+(?:\.\d+)?)\s*(?:Lakh|Lakhs|L)', label, re.I)
    if m_lakh:
        try:
            return int(float(m_lakh.group(1)) * 100000)
        except ValueError:
            pass

    # 3. Match generic trailing digits if Rs is omitted but large number exists
    m_generic = re.search(r'\b(\d{3,10})\b', cleaned)
    if m_generic:
        try:
            return int(m_generic.group(1))
        except ValueError:
            pass

    return None

def process_result_page(result_soup, result_url, result_page_text: str):
    title_text = ""
    title_tag = result_soup.find("h1")
    if title_tag and title_tag.text.strip().lower() not in ["lottery results", "kerala lottery results"]:
        title_text = title_tag.text.strip()
    if not title_text:
        title_tag = result_soup.find("title")
        if title_tag and title_tag.text.strip():
            title_text = title_tag.text.strip()
    if not title_text:
        for tag in ["h2", "h3"]:
            t = result_soup.find(tag)
            if t and t.text.strip():
                title_text = t.text.strip()
                break
    if not title_text:
        title_text = "Unknown Lottery"
    print(f"TITLE TEXT: '{title_text}'")

    # Try to parse date from title; fallback to whole page; finally to today's date if within window
    parsed_date = parse_date_from_text(title_text)
    draw_date = parsed_date.strftime("%Y-%m-%d") if parsed_date else "Unknown-Date"
    if draw_date == "Unknown-Date":
        # Fallback: scan entire page text for a date
        p2 = parse_date_from_text(result_page_text)
        if p2:
            draw_date = p2.strftime("%Y-%m-%d")
        else:
            # As a last resort during the result window, assume today's date
            if is_within_optimal_time_window():
                draw_date = datetime.now(IST).strftime("%Y-%m-%d")

    # Ensure we have today's date if we're in the optimal window and the date is unknown
    if draw_date == "Unknown-Date" and is_within_optimal_time_window():
        draw_date = datetime.now(IST).strftime("%Y-%m-%d")

    draw_number_match = re.search(r"\(([^)]+)\)", title_text)
    draw_number = draw_number_match.group(1) if draw_number_match else "XX"

    lottery_name_match = re.search(r"([A-Za-z\s]+)\s*\(", title_text)
    lottery_name = lottery_name_match.group(1).strip().upper() if lottery_name_match else "Unknown"
    
    lottery_code_match = re.search(r'\(([A-Z]{2,3})\)', title_text)
    lottery_code = lottery_code_match.group(1) if lottery_code_match else 'XX'
    if lottery_code == 'XX' or draw_number == 'XX':
        # Fallback: derive from URL slug like .../kerala-lottery-result-BT-19
        url_slug_match = re.search(r'/([a-z0-9-]*kerala-lottery-result[-/])*([A-Z]{2,3})-(\d+)', result_url)
        if url_slug_match:
            lottery_code = url_slug_match.group(2)
            draw_number = url_slug_match.group(3)
    # Infer lottery code from first winner token if still unknown
    if lottery_code == 'XX':
        # Try scanning for codes like 'DD 781756' in the page text
        mcode = re.search(r'\b([A-Z]{1,3})\s*\d{4,6}\b', result_page_text)
        if mcode:
            lottery_code = mcode.group(1)

    # Try to extract venue
    venue = ""
    venue_tag = result_soup.find(string=re.compile(r"Venue|At", re.I))
    if venue_tag and isinstance(venue_tag, str):
        venue_line = venue_tag.strip()
        venue_match = re.search(r"(?:Venue|At)[:\-]?\s*([A-Za-z0-9, .()]+)", venue_line)
        if venue_match:
            venue = venue_match.group(1).strip()

    # Get download link
    download_link = ""
    for a_tag in result_soup.find_all("a", href=True):
        href = a_tag["href"]
        if any(href.lower().endswith(ext) for ext in [".pdf", ".jpg", ".jpeg", ".png"]):
            if not href.startswith("http"):
                href = "https://www.kllotteryresult.com" + href
            download_link = href
            break

    prizes = {}
    current_key = None
    result_table = result_soup.find("table", class_="w-full")
    if result_table and isinstance(result_table, Tag):
        for row in result_table.find_all("tr"):
            th = row.find("th")
            if th:
                label = th.get_text(strip=True)
                key = None
                for k, v in prize_map.items():
                    if k in label:
                        key = v
                        break
                if key:
                    current_key = key
                    amount = extract_amount_from_label(label)
                    if amount is None:
                        amount = prize_amounts.get(current_key, 0)
                    prizes[current_key] = {
                        "amount": amount,
                        "label": standard_labels.get(current_key, label),
                        "winners": []
                    }
            tds = row.find_all("td")
            if tds and current_key:
                numbers = [td.get_text(strip=True) for td in tds if td.get_text(strip=True)]
                prizes[current_key]["winners"].extend(numbers)

    # Fallback plaintext parsing if no table winners were found
    def parse_plaintext_prizes(txt: str) -> dict:
        lines = [re.sub(r"\s+", " ", ln).strip() for ln in txt.splitlines()]
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
        parsed: Dict[str, Any] = {}
        current_section: Optional[str] = None
        for ln in lines:
            if not ln:
                continue
            
            # Stop parsing completely if we hit a footer/advertisement/upcoming draws block
            should_stop = False
            for kw in stop_keywords:
                if kw in ln.lower():
                    should_stop = True
                    break
            if should_stop:
                break
                
            # Section header detection
            switched = False
            for rgx, key in header_regex_to_key:
                if rgx.search(ln):
                    current_section = key
                    amount = extract_amount_from_label(ln)
                    if current_section not in parsed:
                        if amount is None:
                            amount = prize_amounts.get(current_section, 0)
                        parsed[current_section] = {
                            "amount": amount,
                            "label": standard_labels.get(current_section, current_section.replace('_', ' ').title()),
                            "winners": []
                        }
                    else:
                        if amount is not None and amount > 0:
                            parsed[current_section]["amount"] = amount
                    switched = True
                    break
            if switched:
                continue
            if not current_section:
                continue
            # Skip filler
            if ln.strip() in ("**", "..."):
                continue
            # Extract tokens like 'DD 781756' or plain 4-6 digit numbers
            tokens = re.findall(r"[A-Z]{1,3}\s*\d{4,6}|\b\d{4,6}\b", ln)
            for t in tokens:
                parsed[current_section]["winners"].append(t.strip())
        return parsed

    if not prizes or all(len(section.get("winners", [])) == 0 for section in prizes.values()):
        # Normalize page text from soup to better capture headings and lines
        normalized_text = result_soup.get_text("\n", strip=True)
        parsed_plain = parse_plaintext_prizes(normalized_text)
        if parsed_plain:
            prizes = parsed_plain
            print("Parsed winners using plaintext fallback.")

    # If prizes is empty, initialize with default structure
    if not prizes:
        # Initialize with all prize categories
        for key, label in standard_labels.items():
            prizes[key] = {
                "amount": prize_amounts.get(key, 0),
                "label": label,
                "winners": ["Please wait, results will be published at 3 PM."]
            }
    else:
        # Check if we have actual winning numbers or just placeholders
        has_actual_winners = False
        for key, prize in prizes.items():
            winners = prize["winners"]
            # Check if any winner is not a placeholder
            for winner in winners:
                if winner != "Please wait, results will be published at 3 PM." and winner != "***":
                    has_actual_winners = True
                    break
            if has_actual_winners:
                break
        
        # If we don't have actual winners, use placeholder
        if not has_actual_winners:
            for key, prize in prizes.items():
                prize["winners"] = ["Please wait, results will be published at 3 PM."]
        # Otherwise, de-duplicate and filter draw year, add placeholder to empty categories
        else:
            draw_year = draw_date.split('-')[0] if '-' in draw_date else str(datetime.now(IST).year)
            for key, prize in prizes.items():
                if prize["winners"]:
                    cleaned_winners = []
                    for w in prize["winners"]:
                        w_clean = w.strip()
                        if w_clean != draw_year and w_clean not in cleaned_winners:
                            cleaned_winners.append(w_clean)
                    prize["winners"] = cleaned_winners
                
                if not prize["winners"]:
                    prize["winners"].append("Please wait, results will be published at 3 PM.")

    data = {
        "lottery_name": lottery_name,
        "draw_number": draw_number,
        "draw_date": draw_date,
        "venue": venue,
        "prizes": prizes,
        "downloadLink": download_link
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