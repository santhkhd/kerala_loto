from bs4 import BeautifulSoup

with open('scratch/vishu_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
table = soup.find('table')
if table:
    print("TABLE HTML:")
    print(table.prettify()[:2000]) # First 2000 chars of the table prettified
else:
    print("No table found!")
