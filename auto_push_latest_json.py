<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Kerala Loto: Manual & Auto Push to GitHub</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f7f7f7; color: #222; margin: 0; padding: 0; }
    .container { max-width: 700px; margin: 40px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 12px #0001; padding: 32px; }
    h1 { color: #1a237e; }
    pre, code { background: #f0f0f0; padding: 8px; border-radius: 5px; }
    .step { margin-bottom: 28px; }
    .download-btn {
      display: inline-block; background: #1976d2; color: #fff; padding: 12px 24px; border-radius: 6px;
      text-decoration: none; font-weight: bold; margin-top: 10px; transition: background 0.2s;
    }
    .download-btn:hover { background: #0d47a1; }
    .option { background: #e3f2fd; border-left: 5px solid #1976d2; padding: 18px; margin-bottom: 24px; border-radius: 7px; }
    .auto { background: #e8f5e9; border-left: 5px solid #388e3c; }
    .manual { background: #fffde7; border-left: 5px solid #fbc02d; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Kerala Loto: Manual & Auto Push to GitHub (Replit)</h1>

    <div class="option manual">
      <h2>Manual Push (Replit or Local)</h2>
      <ol>
        <li>
          <b>Download or copy the Python script below</b> and save as <code>generate_latest_json.py</code>.
        </li>
        <li>
          <b>Run the script</b> in your Replit shell:
          <pre><code>python3 generate_latest_json.py</code></pre>
          This will create a JSON file (e.g., <code>KN-581-2025-07-17.json</code>) in your current directory.
        </li>
        <li>
          <b>Move the JSON file to the <code>note/</code> folder</b>:
          <pre><code>mv KN-581-2025-07-17.json note/</code></pre>
        </li>
        <li>
          <b>Push only the JSON file to GitHub</b>:
          <pre><code>
git add note/KN-581-2025-07-17.json
git commit -m "Add latest Kerala lottery result"
git push
          </code></pre>
        </li>
      </ol>
    </div>

    <div class="option auto">
      <h2>Automatic Push (Replit)</h2>
      <ol>
        <li>
          <b>Set your GitHub token as a Replit Secret</b> (key: <code>GITHUB_TOKEN</code>).
        </li>
        <li>
          <b>Use the script below</b> (save as <code>auto_push_latest_json.py</code>).
        </li>
        <li>
          <b>Run the script in Replit</b>:
          <pre><code>python3 auto_push_latest_json.py</code></pre>
          This will:
          <ul>
            <li>Fetch the latest result</li>
            <li>Save it as a JSON file in <code>note/</code></li>
            <li>Automatically push only that file to GitHub</li>
          </ul>
        </li>
      </ol>
    </div>

    <div class="step">
      <h2>Python Script (for both manual and auto push)</h2>
      <p>Copy and use as needed. The script will auto-detect if <code>GITHUB_TOKEN</code> is set and push automatically; otherwise, use manual push.</p>
      <pre><code id="pycode"></code></pre>
    </div>
  </div>
  <script>
    document.getElementById('pycode').textContent = `
import requests
from bs4 import BeautifulSoup
import re
import json
import os
import subprocess
from datetime import datetime

def get_latest_result_link():
    MAIN_URL = "https://www.kllotteryresult.com/"
    res = requests.get(MAIN_URL)
    soup = BeautifulSoup(res.text, "html.parser")
    for a in soup.find_all("a", href=True):
        if re.search(r'/kerala-lottery-result-[A-Z]+-\\d+', a['href']):
            url = a['href']
            if not url.startswith("http"):
                url = "https://www.kllotteryresult.com" + url
            return url
    return None

def process_result_page(result_soup):
    title_tag = result_soup.find("h1")
    title_text = title_tag.text.strip() if title_tag else ""
    date_match = re.search(r"(\\d{2})[./-](\\d{2})[./-](\\d{4})", title_text)
    draw_date = f"{date_match.group(3)}-{date_match.group(2)}-{date_match.group(1)}" if date_match else "Unknown-Date"
    draw_number_match = re.search(r"\\(([^)]+)\\)", title_text)
    draw_number = draw_number_match.group(1) if draw_number_match else "XX"
    lottery_name_match = re.search(r"([A-Za-z\\s]+)\\s*\\(", title_text)
    lottery_name = lottery_name_match.group(1).strip().upper() if lottery_name_match else "Unknown"
    prizes = {}
    result_table = result_soup.find("table", class_="w-full")
    if result_table:
        for row in result_table.find_all("tr"):
            th = row.find("th")
            if th:
                label = th.get_text(strip=True)
                prizes[label] = []
            tds = row.find_all("td")
            if tds and th:
                numbers = [td.get_text(strip=True) for td in tds if td.get_text(strip=True)]
                prizes[label].extend(numbers)
    data = {
        "lottery_name": lottery_name,
        "draw_number": draw_number,
        "draw_date": draw_date,
        "prizes": prizes
    }
    filename = f"note/{draw_number}-{draw_date}.json"
    os.makedirs('note', exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved: {filename}")
    return filename

def auto_git_push(filename):
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("GITHUB_TOKEN not set. Skipping auto push.")
        return
    repo_url = "https://{token}@github.com/santhkhd/kerala_loto.git".format(token=token)
    subprocess.run(["git", "remote", "set-url", "origin", repo_url], check=True)
    subprocess.run(["git", "add", filename], check=True)
    subprocess.run(["git", "commit", "-m", f"Auto update: {filename}"], check=True)
    subprocess.run(["git", "push"], check=True)
    print(f"Pushed {filename} to GitHub.")

if __name__ == "__main__":
    url = get_latest_result_link()
    if url:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        filename = process_result_page(soup)
        if os.environ.get('GITHUB_TOKEN'):
            auto_git_push(filename)
        else:
            print("To auto-push, set GITHUB_TOKEN as a Replit Secret.")
    else:
        print("No latest result found.")
    `.trim();
  </script>
</body>
</html>
