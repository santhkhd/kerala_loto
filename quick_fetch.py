
import updateloto
import requests
from bs4 import BeautifulSoup
import sys

# URL confirmed from homepage
url = "https://www.kllotteryresult.com/kerala-lottery-result-KR-738"

print(f"Fetching {url}...")
try:
    res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    if res.status_code != 200:
        print(f"Failed to fetch: {res.status_code}")
        # Try updateloto robust get
        res = updateloto.robust_get(url, updateloto.HEADERS)
    
    soup = BeautifulSoup(res.text, "html.parser")
    # Call the processing function from the existing module
    updateloto.process_result_page(soup, url, res.text)
    print("Quick update completed.")
except Exception as e:
    print(f"Error: {e}")
