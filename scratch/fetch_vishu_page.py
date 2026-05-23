import requests
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.kllotteryresult.com/'
}

url = 'https://www.kllotteryresult.com/vishu-bumper-br-109-today-result-may-23-2026'
res = requests.get(url, headers=HEADERS)
with open('scratch/vishu_page.html', 'w', encoding='utf-8') as f:
    f.write(res.text)

print("Page fetched successfully.")
