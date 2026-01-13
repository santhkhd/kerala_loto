import os
import json
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scope for Blogger API
SCOPES = ['https://www.googleapis.com/auth/blogger']

# Configuration
BLOG_ID = '6833673542063076265'  # User needs to fill this
TEMPLATE_PATH = r'../androidapp/BLOGGER/blogspotpost.html'
LATEST_RESULT_PATH = r'note/latest.json'
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def get_service():
    """Shows basic usage of the Blogger API.
    Returns the service object.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            os.remove(TOKEN_FILE)
            creds = None
            
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"Error: {CREDENTIALS_FILE} not found. You need to download OAuth 2.0 Client IDs from Google Cloud Console.")
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('blogger', 'v3', credentials=creds)
        return service
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def prepare_post_content():
    # 1. Read Latest Result
    if not os.path.exists(LATEST_RESULT_PATH):
        print("Latest result file not found.")
        return None, None, None

    with open(LATEST_RESULT_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. Read Template
    if not os.path.exists(TEMPLATE_PATH):
        # Try finding it in the current dir if relative path fails
        temp_path_alt = "blogspotpost.html"
        if os.path.exists(temp_path_alt):
             with open(temp_path_alt, 'r', encoding='utf-8') as f:
                template = f.read()
        else:
            print(f"Template not found at {TEMPLATE_PATH}")
            return None, None, None
    else:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template = f.read()

    # 3. Extract Data
    lottery_name = data.get('lottery_name', 'Kerala Lottery')
    draw_number = data.get('draw_number', '')
    date_str = data.get('draw_date', '')
    
    # Generate proper filename for GitHub URL
    # We need to find the filename that matches this result in the note folder
    # Or construct it if we trust the naming convention: CODE-NUMBER-DATE.json
    # The update script saves it as: filename = f"{lottery_code}-{draw_number}-{draw_date}.json"
    # But we don't have lottery_code easily available in latest.json without parsing
    
    # Let's find the file in note dir
    note_dir = 'note'
    target_file_name = ""
    for filename in os.listdir(note_dir):
        if date_str in filename and draw_number in filename and filename.endswith('.json'):
            target_file_name = filename
            break
            
    if not target_file_name:
        print("Could not find specific JSON file for this result.")
        return None, None, None

    json_url = f"https://raw.githubusercontent.com/santhkhd/kerala_loto/master/note/{target_file_name}"

    # 4. Perform Replacements
    content = template.replace('{LOTTERY_NAME}', lottery_name)
    content = content.replace('{DRAW_NUMBER}', draw_number)
    content = content.replace('{DATE}', date_str)
    
    # Replace the placeholder JSON URL with the dynamic one
    # The template has: const jsonUrl = '...'; 
    # We used a dummy URL in the template, so we replace that specific line or variable.
    # A robust way is to replace the whole line defining jsonUrl
    import re
    content = re.sub(
        r"const jsonUrl = 'http[^']+';", 
        f"const jsonUrl = '{json_url}';", 
        content
    )
    # Also catch the specific placeholder user might have or the one from the provided file
    content = content.replace(
        "const jsonUrl = 'https://raw.githubusercontent.com/santhkhd/kerala_loto/refs/heads/main/note/DL-15-2025-08-27.json';",
        f"const jsonUrl = '{json_url}';"
    )

    # 5. Prepare Title and Labels
    title = f"{lottery_name} Lottery Result {date_str} Live Updates"
    labels = ["Kerala Lottery Result", lottery_name, "Lottery Result Today", "Live Results"]

    return title, content, labels

def publish_post(service):
    title, content, labels = prepare_post_content()
    if not title:
        return

    body = {
        "kind": "blogger#post",
        "blog": {
            "id": BLOG_ID
        },
        "title": title,
        "content": content,
        "labels": labels
    }

    try:
        # Check if post already exists to avoid duplicates? 
        # For now, just post.
        posts = service.posts()
        result = posts.insert(blogId=BLOG_ID, body=body).execute()
        print(f"Post published: {result['url']}")
        return True
    except HttpError as error:
        print(f"An error occurred: {error}")
        return False

def main():
    if BLOG_ID == 'YOUR_BLOG_ID_HERE':
        print("Please set your BLOG_ID in the script.")
        return

    service = get_service()
    if service:
        publish_post(service)

if __name__ == '__main__':
    main()
