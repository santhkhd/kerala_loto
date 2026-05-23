import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    url = "https://indialotteryapi.com/wp-json/klr/v1/latest"
    resp = requests.get(url, verify=False, timeout=10)
    data = resp.json()
    print(f"Date: {data.get('draw_date')}")
    print(f"Name: {data.get('draw_name')}")
    print(f"Code: {data.get('draw_code')}")
    # Print the first few prizes to see if they are placeholders
    prizes = data.get('prizes', {})
    print(f"Prizes Found: {list(prizes.keys())}")
    if '1st' in prizes:
        print(f"1st Prize Winners: {prizes['1st']}")
except Exception as e:
    print(f"Error: {e}")
