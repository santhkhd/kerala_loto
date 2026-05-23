import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.kllotteryresult.com/'
}

res = requests.get('https://www.kllotteryresult.com/', headers=HEADERS)
soup = BeautifulSoup(res.text, 'html.parser')
for a in soup.find_all('a', href=True):
    href = a['href'].strip()
    if 'vishu' in href.lower() or 'bumper' in href.lower() or '2026' in href.lower() or 'may-23' in href.lower():
        print(a.text.strip(), "->", href)
