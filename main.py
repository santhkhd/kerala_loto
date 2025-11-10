
import requests
from bs4 import BeautifulSoup, Tag
import json
import re
import time
import os
import subprocess
from datetime import datetime

def get_last_n_result_links(n=50):
    MAIN_URL = "https://www.kllotteryresult.com/"
    links = []
    seen = set()
    next_url = MAIN_URL
    today = datetime.now().date()
    while next_url and len(links) < n:
        res = requests.get(next_url)
        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.find_all("a", href=True):
            if re.search(r'/kerala-lottery-result-[A-Z]+-\d+', a['href']):
                url = a['href']
                if not isinstance(url, str):
                    continue
                if not url.startswith("http"):
                    url = "https://www.kllotteryresult.com" + url
                if url in seen:
                    continue
                try:
                    page_res = requests.get(url)
                    page_soup = BeautifulSoup(page_res.text, "html.parser")
                except Exception:
                    continue
                date_str = None
                # Check multiple date formats and locations
                full_text = page_soup.get_text()
                
                # Try different date patterns
                date_patterns = [
                    r"(\d{2})[./-](\d{2})[./-](\d{4})",  # dd/mm/yyyy
                    r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})",  # d/m/yyyy
                    r"(\d{4})[./-](\d{2})[./-](\d{2})",  # yyyy-mm-dd
                ]
                
                for pattern in date_patterns:
                    m = re.search(pattern, full_text)
                    if m:
                        if len(m.group(1)) == 4:  # yyyy-mm-dd format
                            date_str = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                        else:  # dd/mm/yyyy format
                            date_str = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
                        break
                if date_str:
                    try:
                        result_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        # Allow results from today and recent past (within 15 days)
                        days_diff = (today - result_date).days
                        if days_diff >= -1 and days_diff <= 15:  # Allow tomorrow's date too
                            links.append(url)
                            seen.add(url)
                            if len(links) >= n:
                                break
                    except Exception:
                        # If date parsing fails, still include the result
                        links.append(url)
                        seen.add(url)
                        if len(links) >= n:
                            break
        next_link = soup.find("a", string=re.compile("Older Posts|Next", re.I))
        next_href = next_link.get('href') if isinstance(next_link, Tag) else None
        if next_href and isinstance(next_href, str) and len(links) < n:
            if not next_href.startswith("http"):
                next_url = "https://www.kllotteryresult.com" + next_href
            else:
                next_url = next_href
            time.sleep(1)
        else:
            next_url = None
    return links

# Mappings
prize_map = {
    "1st": "1st_prize", "1st Prize": "1st_prize",
    "Cons": "consolation_prize", "Cons Prize": "consolation_prize",
    "Cons Prize-Rs": "consolation_prize", "Consolation": "consolation_prize",
    "Consolation Prize": "consolation_prize", "2nd": "2nd_prize", "2nd Prize": "2nd_prize",
    "3rd": "3rd_prize", "3rd Prize": "3rd_prize", "4th": "4th_prize", "4th Prize": "4th_prize",
    "5th": "5th_prize", "5th Prize": "5th_prize", "6th": "6th_prize", "6th Prize": "6th_prize",
    "7th": "7th_prize", "7th Prize": "7th_prize", "8th": "8th_prize", "8th Prize": "8th_prize",
    "9th": "9th_prize", "9th Prize": "9th_prize"
}
prize_amounts = {
    "1st_prize": 10000000, "consolation_prize": 5000, "2nd_prize": 3000000,
    "3rd_prize": 500000, "4th_prize": 5000, "5th_prize": 2000,
    "6th_prize": 1000, "7th_prize": 500, "8th_prize": 200, "9th_prize": 100
}
standard_labels = {
    "1st_prize": "1st Prize", "consolation_prize": "Consolation Prize",
    "2nd_prize": "2nd Prize", "3rd_prize": "3rd Prize", "4th_prize": "4th Prize",
    "5th_prize": "5th Prize", "6th_prize": "6th Prize", "7th_prize": "7th Prize",
    "8th_prize": "8th Prize", "9th_prize": "9th Prize"
}

def process_result_page(result_soup, result_url):
    title_text = ""
    title_tag = result_soup.find("h1")
    if title_tag and title_tag.text.strip().lower() not in ["lottery results", "kerala lottery results"]:
        title_text = title_tag.text.strip()
    if not title_text:
        title_tag = result_soup.find("title")
        if title_tag and title_tag.text.strip():
            title_text = title_tag.text.strip()
    if not title_text:
        for tag in ["h2", "h3"]:
            t = result_soup.find(tag)
            if t and t.text.strip():
                title_text = t.text.strip()
                break
    if not title_text:
        title_text = "Unknown Lottery"
    print(f"TITLE TEXT: '{title_text}'")

    date_match = re.search(r"(\d{2})[./-](\d{2})[./-](\d{4})", title_text)
    draw_date = f"{date_match.group(3)}-{date_match.group(2)}-{date_match.group(1)}" if date_match else "Unknown-Date"

    draw_number_match = re.search(r"\(([^)]+)\)", title_text)
    draw_number = draw_number_match.group(1) if draw_number_match else "XX"

    lottery_name_match = re.search(r"([A-Za-z\s]+)\s*\(", title_text)
    lottery_name = lottery_name_match.group(1).strip().upper() if lottery_name_match else "Unknown"

    # Try to extract venue
    venue = ""
    venue_tag = result_soup.find(string=re.compile(r"Venue|At", re.I))
    if venue_tag and isinstance(venue_tag, str):
        venue_line = venue_tag.strip()
        venue_match = re.search(r"(?:Venue|At)[:\-]?\s*([A-Za-z0-9, .()]+)", venue_line)
        if venue_match:
            venue = venue_match.group(1).strip()

    # Get download link
    download_link = ""
    for a_tag in result_soup.find_all("a", href=True):
        href = a_tag["href"]
        if any(href.lower().endswith(ext) for ext in [".pdf", ".jpg", ".jpeg", ".png"]):
            if not href.startswith("http"):
                href = "https://www.kllotteryresult.com" + href
            download_link = href
            break

    prizes = {}
    current_key = None
    result_table = result_soup.find("table", class_="w-full")
    if result_table and isinstance(result_table, Tag):
        for row in result_table.find_all("tr"):
            th = row.find("th")
            if th:
                label = th.get_text(strip=True)
                key = None
                for k, v in prize_map.items():
                    if k in label:
                        key = v
                        break
                if key:
                    current_key = key
                    prizes[current_key] = {
                        "amount": prize_amounts.get(current_key, 0),
                        "label": standard_labels.get(current_key, label),
                        "winners": []
                    }
            tds = row.find_all("td")
            if tds and current_key:
                numbers = [td.get_text(strip=True) for td in tds if td.get_text(strip=True)]
                prizes[current_key]["winners"].extend(numbers)

    for key, prize in prizes.items():
        if not prize["winners"]:
            prize["winners"].append("Please wait, results will be published at 3 PM.")

    data = {
        "lottery_name": lottery_name,
        "draw_number": draw_number,
        "draw_date": draw_date,
        "venue": venue,
        "prizes": prizes,
        "downloadLink": download_link
    }

    filename = f"note/{draw_number}-{draw_date}.json"
    os.makedirs('note', exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved: {filename}\n")
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

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    latest_links = get_last_n_result_links(5)  # Get more results to find today's
    if latest_links:
        print(f"Found {len(latest_links)} recent results")
        for i, result_url in enumerate(latest_links):
            print(f"Processing result {i+1}: {result_url}")
            try:
                result_res = requests.get(result_url)
                result_soup = BeautifulSoup(result_res.text, "html.parser")
                filename = process_result_page(result_soup, result_url)
                if os.environ.get('GITHUB_TOKEN'):
                    auto_git_push(filename)
                else:
                    print("To auto-push, set GITHUB_TOKEN as a Replit Secret.")
            except Exception as e:
                print(f"Error processing {result_url}: {e}")
                continue
    else:
        print("No recent results found.")
