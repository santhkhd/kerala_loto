import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.kllotteryresult.com/'
}

url = 'https://www.kllotteryresult.com/kerala-lottery-result-today'
res = requests.get(url, headers=HEADERS)
with open('scratch/today_live_page.html', 'w', encoding='utf-8') as f:
    f.write(res.text)

soup = BeautifulSoup(res.text, 'html.parser')
text = soup.get_text("\n", strip=True)
with open('scratch/today_live_text.txt', 'w', encoding='utf-8') as f:
    f.write(text)

print("Page fetched and text saved successfully.")
