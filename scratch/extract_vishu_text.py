from bs4 import BeautifulSoup
import re

with open('scratch/vishu_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find all blocks of text that look like they have lottery results
# E.g., containing "1st Prize" or "2nd Prize" and search for lines around them.

text = soup.get_text("\n", strip=True)
lines = text.splitlines()

print(f"Total lines of text: {len(lines)}")

# Let's write the parsed text to a clean text file so we can view it
with open('scratch/vishu_text.txt', 'w', encoding='utf-8') as out_f:
    out_f.write('\n'.join(lines))

print("Text saved to scratch/vishu_text.txt")
