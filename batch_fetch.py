import os
import json
import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup

def fetch_draw_data(draw_code):
    url = f"https://www.kllotteryresult.com/kerala-lottery-result-{draw_code}"
    print(f"Fetching: {url}")
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Parse Title for Date
        title_text = ""
        h1 = soup.find("h1")
        if h1: title_text = h1.text.strip()
        
        m = re.search(r"(\d{2})[./-](\d{2})[./-](\d{4})", title_text)
        if not m:
            print(f"Could not parse date from title: {title_text}")
            return None
        
        draw_date = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        
        # Parse Name & Number
        name_m = re.search(r"([A-Za-z\s\-]+)\s*\(", title_text)
        draw_name = name_m.group(1).strip().upper() if name_m else "Unknown"
        
        parts = draw_code.split("-")
        lottery_code = parts[0]
        draw_number = parts[1]

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
        
        # Specific amounts for some lotteries
        if lottery_code == "BT": prize_amounts["2nd_prize"] = 3000000; prize_amounts["3rd_prize"] = 500000
        if lottery_code == "KR": prize_amounts["3rd_prize"] = 1000000
        if lottery_code == "DL": prize_amounts["2nd_prize"] = 3000000; prize_amounts["3rd_prize"] = 500000

        table = soup.find("table", class_="w-full") # Adjusted selector based on updateloto.py
        if not table:
             table = soup.find("table") # fallback

        if table:
            current_key = None
            for row in table.find_all("tr"):
                th = row.find("th")
                if th:
                    label = th.get_text(strip=True)
                    for k, v in prize_map.items():
                        if k in label:
                            current_key = v
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
                    raw_nums = tds[0].get_text(strip=True).split() if len(tds) == 1 else [td.get_text(strip=True) for td in tds]
                    # Updateloto logic used tds loop. Let's stick to what works.
                    nums = [n for n in raw_nums if n]
                    prizes[current_key]["winners"].extend(nums)
        
        if not prizes: return None

        return {
            "lottery_name": draw_name,
            "draw_number": draw_number,
            "draw_date": draw_date,
            "venue": "GORKY BHAVAN NEAR BAKERY JUNCTION THIRUVANANTHAPURAM",
            "prizes": prizes,
            "draw_code": draw_code,
            "downloadLink": ""
        }
    except Exception as e:
        print(f"Error fetching {draw_code}: {e}")
        return None

def main():
    draws = [
        "SS-506", "DL-39", "KN-610", "SK-40", "KR-742", "SM-42", "BT-41",
        "SS-507", "DL-40", "KN-611", "SK-41", "KR-743", "SM-43", "BT-42"
    ]
    
    for code in draws:
        data = fetch_draw_data(code)
        if data:
            filename = f"{data['draw_code']}-{data['draw_date']}.json"
            path = f"note/{filename}"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Saved: {path}")
        else:
            print(f"Failed to fetch: {code}")

if __name__ == "__main__":
    main()
