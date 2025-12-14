import requests
from bs4 import BeautifulSoup, Tag
import json
import re
import time
from datetime import datetime, timedelta
import os

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
                for tag in ["h1", "title", "h2", "h3"]:
                    t = page_soup.find(tag)
                    if t and t.text:
                        m = re.search(r"(\d{2})[./-](\d{2})[./-](\d{4})", t.text)
                        if m:
                            date_str = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
                            break
                if date_str:
                    try:
                        result_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        # Allow results up to tomorrow
                        if result_date <= today + timedelta(days=1):
                            links.append(url)
                            seen.add(url)
                            if len(links) >= n:
                                break
                    except Exception:
                        continue
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
    "5th_prize": "5th Prize", "6th_prize": "6th Prize", "7th_prize": "7th_prize",
    "8th_prize": "8th Prize", "9th_prize": "9th Prize"
}

def process_result_page(result_url):
    try:
        result_res = requests.get(result_url)
        result_soup = BeautifulSoup(result_res.text, "html.parser")
    except Exception as e:
        print(f"Error fetching or parsing {result_url}: {e}")
        return

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
    print(f"Processing '{title_text}' from {result_url}")

    date_match = re.search(r"(\d{2})[./-](\d{2})[./-](\d{4})", title_text)
    draw_date = f"{date_match.group(3)}-{date_match.group(2)}-{date_match.group(1)}" if date_match else "Unknown-Date"

    draw_number_match = re.search(r"\(([^)]+)\)", title_text)
    draw_number = draw_number_match.group(1) if draw_number_match else "XX"

    lottery_name_match = re.search(r"([A-Za-z\s]+)\s*\(", title_text)
    lottery_name = lottery_name_match.group(1).strip().upper() if lottery_name_match else "Unknown"
    
    # Extract lottery code from URL
    lottery_code_match = re.search(r'/kerala-lottery-result-([A-Z]+)-', result_url)
    lottery_code = lottery_code_match.group(1) if lottery_code_match else "XX"

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

    # If no prizes found, initialize with default structure
    if not prizes:
        for key, label in standard_labels.items():
            prizes[key] = {
                "amount": prize_amounts.get(key, 0),
                "label": label,
                "winners": ["Please wait, results will be published at 3 PM."]
            }
    else:
        # Add "Please wait" message to any prize category that has no winners
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

    # Create note directory if it doesn't exist
    os.makedirs('note', exist_ok=True)
    
    # Generate filename in the correct format (e.g., SS-485-2025-09-16.json)
    # Remove the duplicate lottery code from draw_number if present
    clean_draw_number = draw_number
    if draw_number.startswith(lottery_code + "-"):
        clean_draw_number = draw_number[len(lottery_code) + 1:]
    
    filename = f"{lottery_code}-{clean_draw_number}-{draw_date}.json"
    filepath = f"note/{filename}"
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved: {filepath}\n")
    except Exception as e:
        print(f"Error saving {filepath}: {e}")


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("Fetching latest results from website...")
    # Fetch last 30 to be safe and cover the gap
    urls_to_process = get_last_n_result_links(30)
    
    if not urls_to_process:
        print("No URLs found to process.")
    else:
        # Process each URL
        print(f"Found {len(urls_to_process)} links to process.")
        for i, url in enumerate(urls_to_process, 1):
            print(f"Processing {i}/{len(urls_to_process)}: {url}")
            process_result_page(url)
            time.sleep(1)  # Be respectful to the server

    print("All lottery results have been downloaded to the 'note' folder.")