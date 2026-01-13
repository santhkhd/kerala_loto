import os
import json
import re
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
BLOG_ID = '6833673542063076265'
TEMPLATE_PATH = r'../androidapp/BLOGGER/blogspotpost.html'
NOTE_DIR = r'note'
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'

SCOPES = ['https://www.googleapis.com/auth/blogger']

def get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except:
            os.remove(TOKEN_FILE)
            creds = None
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"Error: {CREDENTIALS_FILE} not found.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('blogger', 'v3', credentials=creds)

def prepare_content(json_path, template):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    lottery_name = data.get('lottery_name', 'Kerala Lottery')
    draw_number = data.get('draw_number', '')
    date_str = data.get('draw_date', '')
    
    # 1. Backdate Logic
    try:
        publish_date = datetime.strptime(date_str, "%Y-%m-%d").isoformat() + "Z"
    except:
        publish_date = datetime.now().isoformat() + "Z"

    # 2. Get Filename for URL
    filename = os.path.basename(json_path)
    json_url = f"https://raw.githubusercontent.com/santhkhd/kerala_loto/master/note/{filename}"

    # 3. Code Logic
    full_draw_code = data.get('draw_code', '')
    
    # Clean up double prefixes if they exist (e.g. XX-BT-26 -> BT-26)
    if full_draw_code.startswith("XX-") and len(full_draw_code) > 6:
         # If it looks like XX-BT-26, strip the XX-
         full_draw_code = full_draw_code.replace("XX-", "")

    # If code is missing or completely generic (just "XX-Number")
    if not full_draw_code or full_draw_code.startswith("XX-"):
        code_map = {
            "STHREE SAKTHI": "SS", "AKSHAYA": "AK", "KARUNYA PLUS": "KN",
            "KARUNYA": "KR", "NIRMAL": "NR", "FIFTY FIFTY": "FF", "WIN WIN": "W",
            "BHAGYATHARA": "BT" 
        }
        
        # Default prefix
        prefix = "XX"
        
        # Try to match name
        for name, code in code_map.items():
            if name in lottery_name.upper():
                prefix = code
                break
        
        # Reconstruct: If we found a valid prefix (not XX), use it
        if prefix != "XX":
             # Check if draw_number already has the prefix (e.g. KN-598)
             if draw_number.startswith(prefix):
                 full_draw_code = draw_number
             else:
                 full_draw_code = f"{prefix}-{draw_number}"

    # 4. Replacements
    content = template.replace('{LOTTERY_NAME}', lottery_name)
    content = content.replace('{DRAW_NUMBER}', draw_number)
    content = content.replace('{DATE}', date_str)
    
    content = re.sub(r"const jsonUrl = 'http[^']+';", f"const jsonUrl = '{json_url}';", content)
    content = content.replace(
        "const jsonUrl = 'https://raw.githubusercontent.com/santhkhd/kerala_loto/refs/heads/main/note/DL-15-2025-08-27.json';",
        f"const jsonUrl = '{json_url}';"
    )

    title = f"{lottery_name.upper()},{full_draw_code}"
    labels = ["Kerala Lottery Result", lottery_name, full_draw_code]
    
    return title, content, labels, publish_date

def main():
    service = get_service()
    if not service: return

    # Read Template
    if not os.path.exists(TEMPLATE_PATH):
        # Fallback local check
        if os.path.exists("blogspotpost.html"):
            with open("blogspotpost.html", 'r', encoding='utf-8') as f: template = f.read()
        else:
            print("Template not found")
            return
    else:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template = f.read()

    # Iterate over all JSON files in note directory
    files = [f for f in os.listdir(NOTE_DIR) if f.endswith('.json') and f != 'latest.json']
    print(f"Found {len(files)} past results to publish...")

    count = 0
    for filename in files:
        # Check if already published? (This is hard without tracking, but Blogger allows duplicates)
        # We will just publish them. Be careful running this multiple times.
        
        path = os.path.join(NOTE_DIR, filename)
        title, content, labels, pub_date = prepare_content(path, template)
        
        body = {
            "kind": "blogger#post",
            "blog": {"id": BLOG_ID},
            "title": title,
            "content": content,
            "labels": labels,
            "published": pub_date # This is the magic key for backdating
        }
        
        try:
            service.posts().insert(blogId=BLOG_ID, body=body).execute()
            print(f"[{count+1}/{len(files)}] Published: {title} on {pub_date}")
            count += 1
        except HttpError as e:
            print(f"Error publishing {filename}: {e}")
            
    print("Batch publishing complete.")

if __name__ == "__main__":
    main()
