import os
import json
import requests
import re
import urllib3
from datetime import datetime

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://indialotteryapi.com/wp-json/klr/v1/latest"

def fetch_latest_result():
    try:
        print(f"Fetching data from {API_URL}...")
        resp = requests.get(API_URL, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error fetching API: {e}")
        return None

def process_and_save(data):
    if not data:
        print("No data received.")
        return False

    # Extract Basic Info
    draw_date = data.get("draw_date")
    draw_name = data.get("draw_name", "Unknown").upper()
    full_code = data.get("draw_code", "XX-00")
    
    # Split Code (e.g. BT-37 -> BT, 37)
    if "-" in full_code:
        parts = full_code.split("-")
        lottery_code = parts[0]
        draw_number = parts[1] if len(parts) > 1 else "00"
    else:
        # Fallback simple split
        lottery_code = full_code[:2]
        draw_number = full_code[2:]
        
    prizes_data = data.get("prizes", {})
    first_data = data.get("first", {})
    amounts_map = prizes_data.get("amounts", {})
    
    final_prizes = {}
    
    # 1. First Prize Construction
    if first_data:
        winner = first_data.get("ticket", "")
        loc = first_data.get("location", "")
        # Format: "Ticket (Location)"
        if loc:
            winner += f" ({loc})"
        
        final_prizes["1st_prize"] = {
            "amount": 10000000, 
            "label": "1st Prize",
            "winners": [winner] if winner else ["Wait"]
        }
    else:
         final_prizes["1st_prize"] = {
            "amount": 10000000, 
            "label": "1st Prize",
            "winners": ["Wait"]
        }

    # 2. Other Prizes Mapping
    # API key -> My Schema Key
    key_map = {
        "consolation": "consolation_prize",
        "2nd": "2nd_prize",
        "3rd": "3rd_prize",
        "4th": "4th_prize",
        "5th": "5th_prize",
        "6th": "6th_prize",
        "7th": "7th_prize",
        "8th": "8th_prize", 
        "9th": "9th_prize"
    }
    
    # Default amounts if API doesn't specify or we fail to parse
    std_amounts = {
        "consolation_prize": 5000, "2nd_prize": 3000000, "3rd_prize": 500000,
        "4th_prize": 5000, "5th_prize": 2000, "6th_prize": 1000,
        "7th_prize": 500, "8th_prize": 200, "9th_prize": 100
    }
    
    for api_key, my_key in key_map.items():
        # Check if this prize category exists in API response
        # Sometimes keys might be missing if no winners yet
        winners = prizes_data.get(api_key, [])
        
        # Ensure winners is a list
        if isinstance(winners, str): winners = [winners]
        
        # If winners list is empty, put a placeholder? Or leave empty?
        # App expects winners.
        if not winners:
            winners = [] # Empty list implies no winners declared yet
            
        # Parse Amount
        amt_val = 0
        if api_key in amounts_map:
            amt_str = amounts_map[api_key]
            # "₹1,00,00,000/-" -> 10000000
            try:
                amt_val = int(re.sub(r"[^\d]", "", amt_str))
            except:
                amt_val = std_amounts.get(my_key, 0)
        else:
            amt_val = std_amounts.get(my_key, 0)

        # Label Construction
        if api_key == "consolation":
            label = "Consolation Prize"
        else:
            # "2nd" -> "2nd Prize"
            label = api_key.capitalize() + " Prize"

        final_prizes[my_key] = {
            "amount": amt_val,
            "label": label,
            "winners": winners
        }
            
    # Output Object
    output = {
        "lottery_name": draw_name,
        "draw_number": draw_number,
        "draw_date": draw_date,
        "venue": "GORKY BHAVAN NEAR BAKERY JUNCTION THIRUVANANTHAPURAM",
        "prizes": final_prizes,
        "downloadLink": "" # API does not provide this yet
    }
    
    # Create note directory
    os.makedirs('note', exist_ok=True)
    
    # Generate Filename
    filename = f"{lottery_code}-{draw_number}-{draw_date}.json"
    local_path = f"note/{filename}"
    
    # Save Specific Result
    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Saved result to: {os.path.abspath(local_path)}")
        
    # Save Latest
    latest_path = "note/latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Updated latest.json at: {os.path.abspath(latest_path)}")
    
    return True

def main():
    print("--- Starting API-based Lottery Update ---")
    data = fetch_latest_result()
    if data:
        process_and_save(data)
    else:
        print("Failed to update from API.")
        
    # Always update a status file so we know the scheduler is running
    status = {
        "last_check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "active"
    }
    with open("status.json", "w") as f:
        json.dump(status, f)

if __name__ == "__main__":
    main()