from bs4 import BeautifulSoup

with open('scratch/vishu_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
table = soup.find('table')
if table:
    with open('scratch/vishu_table.txt', 'w', encoding='utf-8') as out_f:
        out_f.write(table.prettify())
    print("Table saved to scratch/vishu_table.txt")
else:
    print("No table found!")
