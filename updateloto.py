import os
import json
import requests
import re
import urllib3
from datetime import datetime
from bs4 import BeautifulSoup, Tag
from typing import Optional, Dict, Any

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
        resp = requests.get(
            API_URL,
            headers={'User-Agent': 'Mozilla/5.0'},
            verify=False,
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    except Exception as e:
        print(f"API Error: {e}")
        return None


# Prize mappings
prize_map = {
    "1st": "1st_prize",
    "1st Prize": "1st_prize",
    "Cons": "consolation_prize",
    "Cons Prize": "consolation_prize",
    "Cons Prize-Rs": "consolation_prize",
    "Consolation": "consolation_prize",
    "Consolation Prize": "consolation_prize",
    "2nd": "2nd_prize",
    "2nd Prize": "2nd_prize",
    "3rd": "3rd_prize",
    "3rd Prize": "3rd_prize",
    "4th": "4th_prize",
    "4th Prize": "4th_prize",
    "5th": "5th_prize",
    "5th Prize": "5th_prize",
    "6th": "6th_prize",
    "6th Prize": "6th_prize",
    "7th": "7th_prize",
    "7th Prize": "7th_prize",
    "8th": "8th_prize",
    "8th Prize": "8th_prize",
    "9th": "9th_prize",
    "9th Prize": "9th_prize"
}

prize_amounts = {
    "1st_prize": 10000000,
    "consolation_prize": 5000,
    "2nd_prize": 3000000,
    "3rd_prize": 500000,
    "4th_prize": 5000,
    "5th_prize": 2000,
    "6th_prize": 1000,
    "7th_prize": 500,
    "8th_prize": 200,
    "9th_prize": 100
}

standard_labels = {
    "1st_prize": "1st Prize",
    "consolation_prize": "Consolation Prize",
    "2nd_prize": "2nd Prize",
    "3rd_prize": "3rd Prize",
    "4th_prize": "4th Prize",
    "5th_prize": "5th Prize",
    "6th_prize": "6th Prize",
    "7th_prize": "7th Prize",
    "8th_prize": "8th Prize",
    "9th_prize": "9th Prize"
}


def extract_amount_from_label(label: str) -> Optional[int]:
    if not label:
        return None

    cleaned = re.sub(r'[\s,\-/\\]', '', label)

    # Rs patterns
    m_rs = re.search(r'(?:Rs|Rs\.|Rs:)\s*[:\.]?\s*(\d+)', cleaned, re.I)
    if m_rs:
        try:
            return int(m_rs.group(1))
        except ValueError:
            pass

    # Crore
    m_crore = re.search(r'(\d+(?:\.\d+)?)\s*(?:Crore|Crores|Cr)', label, re.I)
    if m_crore:
        try:
            return int(float(m_crore.group(1)) * 10000000)
        except ValueError:
            pass

    # Lakh
    m_lakh = re.search(r'(\d+(?:\.\d+)?)\s*(?:Lakh|Lakhs|L)', label, re.I)
    if m_lakh:
        try:
            return int(float(m_lakh.group(1)) * 100000)
        except ValueError:
            pass

    # Generic digits
    m_generic = re.search(r'\b(\d{3,10})\b', cleaned)
    if m_generic:
        try:
            return int(m_generic.group(1))
        except ValueError:
            pass

    return None


def parse_api_data(data):
    if not data:
        return None

    draw_date = data.get("draw_date")
    draw_name = data.get("draw_name", "Unknown").upper()
    full_code = data.get("draw_code", "XX-00")

    parts = full_code.split("-") if "-" in full_code else [full_code[:2], full_code[2:]]

    lottery_code = parts[0]
    draw_number = parts[1] if len(parts) > 1 else "00"

    prizes_data = data.get("prizes", {})
    amounts_map = prizes_data.get("amounts", {})

    final_prizes = {}

    std_amounts = {
        "consolation": 5000,
        "2nd": 3000000,
        "3rd": 500000,
        "4th": 5000,
        "5th": 2000,
        "6th": 1000,
        "7th": 500,
        "8th": 200,
        "9th": 100
    }

    ignore = ["amounts", "guess", "mc"]

    for api_key, val in prizes_data.items():

        if api_key in ignore:
            continue

        my_key = "consolation_prize" if api_key == "consolation" else f"{api_key}_prize"

        label = (
            "Consolation Prize"
            if api_key == "consolation"
            else f"{api_key.capitalize()} Prize"
        )

        winners = val if isinstance(val, list) else [val] if val else []

        amt_val = std_amounts.get(api_key, 0)

        if api_key in amounts_map:
            try:
                amt_val = int(re.sub(r"[^\d]", "", str(amounts_map[api_key])))
            except:
                pass

        final_prizes[my_key] = {
            "amount": amt_val,
            "label": label,
            "winners": winners
        }

    return {
        "lottery_name": draw_name,
        "draw_number": draw_number,
        "lottery_code": lottery_code,
        "draw_date": draw_date,
        "prizes": final_prizes,
        "source": "API"
    }


# ==========================================
# 2. WEB FALLBACK METHOD
# ==========================================
def fetch_web_data():

    try:
        print(f"Checking Fallback Web: {WEB_URL}...")

        res = requests.get(
            WEB_URL,
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=30
        )

        soup = BeautifulSoup(res.text, "html.parser")

        link = None

        for a in soup.find_all("a", href=True):

            if re.search(r'/kerala-lottery-result-[A-Z]+-\d+', a['href']):

                link = a['href']

                if not link.startswith("http"):
                    link = "https://www.kllotteryresult.com" + link

                break

        if not link:
            print("Fallback: No result links found.")
            return None

        print(f"Fallback: Fetching {link}...")

        p_res = requests.get(
            link,
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=30
        )

        p_soup = BeautifulSoup(p_res.text, "html.parser")

        title_text = ""

        h1 = p_soup.find("h1")

        if h1:
            title_text = h1.text.strip()

        m = re.search(r"(\d{2})[./-](\d{2})[./-](\d{4})", title_text)

        if not m:
            print("Fallback: Could not parse date from title.")
            return None

        draw_date = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

        name_m = re.search(r"([A-Za-z\s]+)\s*\(", title_text)

        draw_name = name_m.group(1).strip().upper() if name_m else "Unknown"

        num_m = re.search(r"\(([^)]+)\)", title_text)

        full_code = num_m.group(1) if num_m else "XX-00"

        parts = (
            full_code.split("-")
            if "-" in full_code
            else [full_code[:2], full_code[2:]]
        )

        lottery_code = parts[0]
        draw_number = parts[1] if len(parts) > 1 else "00"

        prizes = {}

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

                            clean_label = standard_labels.get(current_key, label)

                            amount = extract_amount_from_label(label)

                            if amount is None:
                                amount = prize_amounts.get(current_key, 0)

                            prizes[current_key] = {
                                "amount": amount,
                                "label": clean_label,
                                "winners": []
                            }

                            break

                tds = row.find_all("td")

                if tds and current_key:

                    nums = [
                        td.get_text(strip=True)
                        for td in tds
                        if td.get_text(strip=True)
                    ]

                    prizes[current_key]["winners"].extend(nums)

        if not prizes:
            return None

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
# 3. SAVE DATA
# ==========================================
def save_data(data):

    if not data:
        return False

    output = {
        "lottery_name": data["lottery_name"],
        "draw_number": data["draw_number"],
        "draw_date": data["draw_date"],
        "venue": "GORKY BHAVAN NEAR BAKERY JUNCTION THIRUVANANTHAPURAM",
        "prizes": data["prizes"],
        "draw_code": f"{data['lottery_code']}-{data['draw_number']}",
        "downloadLink": ""
    }

    os.makedirs('note', exist_ok=True)

    filename = (
        f"{data['lottery_code']}-"
        f"{data['draw_number']}-"
        f"{data['draw_date']}.json"
    )

    local_path = f"note/{filename}"

    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Saved: {local_path}")

    with open("note/latest.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("Updated note/latest.json")

    return True


# ==========================================
# MAIN
# ==========================================
def main():

    today = get_today_date_str()

    print(f"--- Starting Update (Today: {today}) ---")

    api_raw = fetch_api_data()

    api_clean = parse_api_data(api_raw)

    if api_clean and api_clean['draw_date'] == today:

        print("API has today's result!")

        save_data(api_clean)

    else:

        print(
            f"API result date "
            f"({api_clean['draw_date'] if api_clean else 'None'}) "
            f"is not today."
        )

        print("Attempting Fallback Request...")

        web_clean = fetch_web_data()

        if web_clean and web_clean['draw_date'] == today:

            print("Fallback Web has today's result!")

            save_data(web_clean)

        else:

            print(
                f"Fallback Web date "
                f"({web_clean['draw_date'] if web_clean else 'None'}) "
                f"is also not today."
            )

            print("No update performed.")

    with open("status.json", "w") as f:
        json.dump(
            {
                "last_check": today,
                "status": "checked"
            },
            f
        )


if __name__ == "__main__":
    main()
