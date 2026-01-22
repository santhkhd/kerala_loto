import requests
import urllib3
urllib3.disable_warnings()

print("--- Probing API for 2026-01-15 ---")
url = "https://indialotteryapi.com/wp-json/klr/v1/latest"
try:
    r = requests.get(url, verify=False, timeout=10)
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Date: {data.get('draw_date')}")
    print(f"Code: {data.get('draw_code')}")
except Exception as e:
    print(f"Error: {e}")
