from bs4 import BeautifulSoup

with open('scratch/vishu_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
tables = soup.find_all('table')
print(f"Found {len(tables)} tables:")
for idx, table in enumerate(tables):
    print(f"Table {idx}: class={table.get('class')}")
    # Print the first few rows
    for r_idx, row in enumerate(table.find_all('tr')[:5]):
        print(f"  Row {r_idx}: {[td.text.strip() for td in row.find_all(['td', 'th'])]}")
