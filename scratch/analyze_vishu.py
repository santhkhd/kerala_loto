import json
from bs4 import BeautifulSoup

with open('scratch/vishu_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

output = []

# 1. Print page title
title = soup.title.text if soup.title else 'No Title'
output.append(f"Title: {title}")

h1 = soup.find('h1')
output.append(f"H1: {h1.text.strip() if h1 else 'No H1'}")

# 2. Let's find the main table
tables = soup.find_all('table')
output.append(f"Found {len(tables)} tables")

for idx, table in enumerate(tables):
    output.append(f"\n--- TABLE {idx} ---")
    rows = table.find_all('tr')
    output.append(f"Table has {len(rows)} rows")
    for r_idx, row in enumerate(rows[:50]): # Let's look at first 50 rows
        th = row.find('th')
        tds = row.find_all('td')
        th_text = th.text.strip() if th else 'None'
        tds_text = [td.text.strip() for td in tds]
        output.append(f"Row {r_idx}: TH='{th_text}' | TDs={tds_text}")

with open('scratch/vishu_analysis.txt', 'w', encoding='utf-8') as out_f:
    out_f.write('\n'.join(output))

print("Analysis saved to scratch/vishu_analysis.txt")
