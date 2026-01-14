import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

url = "https://www.kllotteryresult.com/kerala-lottery-result-DL-35"
print(f"Checking {url}")
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(r.text, "html.parser")

table = soup.find("table", class_="w-full")
if table:
    print("Found table.")
    for row in table.find_all("tr"):
        th = row.find("th")
        if th and ("8th" in th.text or "9th" in th.text):
            print(f"--- {th.text.strip()} ---")
            tds = row.find_all("td")
            nums = [td.text.strip() for td in tds]
            print(nums[:10]) # Print first 10 winners
else:
    print("No table found.")
