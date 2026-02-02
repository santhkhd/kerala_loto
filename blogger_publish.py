import os
import json
import datetime
import random
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scope for Blogger API
SCOPES = ['https://www.googleapis.com/auth/blogger']

# Configuration
BLOG_ID = '6833673542063076265'
TEMPLATE_PATH = r'../androidapp/BLOGGER/blogspotpost.html'
LATEST_RESULT_PATH = r'note/latest.json'
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def get_service():
    """Shows basic usage of the Blogger API.
    Returns the service object.
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            os.remove(TOKEN_FILE)
            creds = None
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                creds = None
        
        if not creds or not creds.valid:
            if os.environ.get('GITHUB_ACTIONS'):
                print("ERROR: BLOGGER_TOKEN_JSON is expired or invalid.")
                print("Please run this script locally to generate a new token.json and update your GitHub Secret.")
                return None
                
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"Error: {CREDENTIALS_FILE} not found. Download OAuth 2.0 Client IDs.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

    try:
        service = build('blogger', 'v3', credentials=creds)
        return service
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def generate_rich_seo_content(lname, dcode, dnum, ddate, prizes):
    """Generates unique SEO-rich article content to append to the post."""
    
    first_prize_amt = "₹1 Crore" # Default fallback
    if prizes and isinstance(prizes, list) and len(prizes) > 0:
        try:
             val = str(prizes[0].get('amount', ''))
             if val == "7500000": first_prize_amt = "₹75 Lakhs"
             elif val == "10000000": first_prize_amt = "₹1 Crore"
             elif val == "7000000": first_prize_amt = "₹70 Lakhs"
             elif val == "8000000": first_prize_amt = "₹80 Lakhs"
             elif len(val) > 4: first_prize_amt = f"₹{val}"
        except:
             pass

    intros = [
        f"The Kerala State Lottery Department has officially announced the results for the <b>{lname} {dnum}</b> draw held on {ddate}. Thousands of participants across the state have been eagerly waiting for this moment.",
        f"The live results for the <b>{lname}</b> lottery (Code: {dnum}) are now available. Conducted by the Kerala Government, this draw offers a massive First Prize of {first_prize_amt}.",
        f"Today's {lname} lottery result has been declared at Gorky Bhavan, Thiruvananthapuram. Participants can now check the official list of winning numbers below."
    ]
    
    body_text = f"""
    <div style="margin-top: 50px; padding-top: 30px; border-top: 1px solid #e2e8f0; font-family: 'Inter', sans-serif; color: #334155; line-height: 1.8;">
        <h2 style="font-size: 1.6rem; font-weight: 800; color: #1e293b; margin-bottom: 20px;">
            {lname} {dnum} Lottery Result Analysis
        </h2>
        
        <p>{random.choice(intros)}</p>

        <h3 style="font-size: 1.3rem; font-weight: 700; color: #3b82f6; margin-top: 30px; margin-bottom: 12px;">
            Prize Breakdown & Winning Details
        </h3>
        <p>
            The highlight of today's draw is undoubtedly the 1st Prize of <b>{first_prize_amt}</b>. 
            Additionally, there are attractive prizes for the 2nd position (₹10 Lakhs) and 3rd position (₹5,000 for 12 winners per series). 
            Even if you missed the jackpot, don't forget to check the last 4 digits of your ticket against the consolidation and lower-tier prize lists.
        </p>

        <div style="background: #f1f5f9; padding: 24px; border-radius: 16px; margin: 30px 0;">
            <h4 style="margin: 0 0 12px 0; font-size: 1.1rem; color: #0f172a;">📝 How to Claim Your Prize</h4>
            <ul style="margin: 0; padding-left: 20px; color: #475569;">
                <li style="margin-bottom: 8px;"><b>Winnings up to ₹5,000:</b> Can be claimed from any authorized lottery stall.</li>
                <li style="margin-bottom: 8px;"><b>Winnings above ₹5,000:</b> Must be surrendered to the Director of State Lotteries or a Nationalized Bank along with ID proof (Aadhar/PAN).</li>
                <li style="margin-bottom: 8px;"><b>Validity:</b> Ensure you claim your prize within <b>30 days</b> of the draw date.</li>
                <li><b>Ticket Condition:</b> Keep your ticket safe and untorn. Damaged tickets may be rejected.</li>
            </ul>
        </div>

        <h3 style="font-size: 1.3rem; font-weight: 700; color: #3b82f6; margin-top: 30px; margin-bottom: 12px;">
            Next Draw Schedule
        </h3>
        <p>
            Kerala Lotteries conducts draws seven days a week. Be sure to check back tomorrow at 3:00 PM for the live updates of the next lucky draw. 
            We provide the fastest and most accurate result updates directly from the draw venue.
        </p>
        
        <p style="margin-top: 40px; font-size: 0.9rem; color: #94a3b8; font-style: italic; border-top: 1px dashed #cbd5e1; padding-top: 20px;">
            <strong>Disclaimer:</strong> This website is an informational platform and is not officially affiliated with the Government of Kerala. 
            While we strive for accuracy, please verify your winning numbers with the Kerala Government Gazette before making any claims.
        </p>
    </div>
    """
    return body_text

def prepare_post_content():
    if not os.path.exists(LATEST_RESULT_PATH):
        print("Latest result file not found.")
        return None, None, None

    with open(LATEST_RESULT_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not os.path.exists(TEMPLATE_PATH):
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

    lottery_name = data.get('lottery_name', 'Kerala Lottery')
    draw_number = data.get('draw_number', '')
    date_str = data.get('draw_date', '')
    
    # Locate JSON file URL
    note_dir = 'note'
    target_file_name = ""
    # Smart search for matching JSON file
    if os.path.exists(note_dir):
        for filename in os.listdir(note_dir):
            if date_str in filename and draw_number in filename and filename.endswith('.json'):
                target_file_name = filename
                break
    
    if not target_file_name:
        # Fallback to constructing it if finding fails
        # Assuming filename format: CODE-NUMBER-DATE.json
        pass
        
    json_url = f"https://raw.githubusercontent.com/santhkhd/kerala_loto/master/note/{target_file_name}" if target_file_name else ""

    # Basic String Replacements
    content = template.replace('{LOTTERY_NAME}', lottery_name)
    content = content.replace('{DRAW_NUMBER}', draw_number)
    content = content.replace('{DATE}', date_str)
    
    # Smart JSON URL Replacement
    import re
    # Matches typical JS line: const jsonUrl = '...';
    content = re.sub(r"const jsonUrl = '[^']+';", f"const jsonUrl = '{json_url}';", content)

    # Determine Full Code
    full_draw_code = data.get('draw_code', '')
    if full_draw_code.startswith("XX-") and len(full_draw_code) > 6:
        full_draw_code = full_draw_code.replace("XX-", "")

    if not full_draw_code or full_draw_code.startswith("XX-"):
        code_map = {
            "STHREE SAKTHI": "SS", "AKSHAYA": "AK", "KARUNYA PLUS": "KN",
            "KARUNYA": "KR", "NIRMAL": "NR", "FIFTY FIFTY": "FF",
            "WIN WIN": "W", "BHAGYATHARA": "BT"
        }
        prefix = "XX"
        name_upper = lottery_name.upper()
        for name, code in code_map.items():
            if name in name_upper:
                prefix = code
                break
        if prefix != "XX":     
            if draw_number.startswith(prefix): full_draw_code = draw_number
            else: full_draw_code = f"{prefix}-{draw_number}"

    # --- ADD RICH SEO CONTENT ---
    seo_content = generate_rich_seo_content(lottery_name, full_draw_code, draw_number, date_str, data.get('prizes', []))
    content += seo_content
    # ----------------------------

    title = f"{lottery_name.upper()},{full_draw_code}"
    labels = ["Kerala Lottery Result", lottery_name, "Lottery Result Today", "Live Results", full_draw_code]

    return title, content, labels

def publish_post(service):
    title, content, labels = prepare_post_content()
    if not title: return

    # --- SHOW TEST OUTPUT ---
    print("\n--- [PREVIEW: GENERATED SEO CONTENT] ---")
    print(f"TITLE: {title}")
    # Show glimpse of appended content (last 500 chars which contains the new SEO text)
    preview_len = len(content)
    snippet_start = max(0, preview_len - 1500)
    print(content[snippet_start:]) 
    print("----------------------------------------\n")
    # ------------------------

    body = {
        "kind": "blogger#post",
        "blog": {"id": BLOG_ID},
        "title": title,
        "content": content,
        "labels": labels
    }

    try:
        posts = service.posts()
        list_response = posts.list(blogId=BLOG_ID, maxResults=20, fetchBodies=True).execute()
        
        existing_post = None
        for post in list_response.get('items', []):
            if post['title'].strip() == title.strip():
                existing_post = post
                break
        
        if existing_post:
            print(f"Found existing post: '{title}'. Updating content...")
            # Update the existing post
            result = posts.update(blogId=BLOG_ID, postId=existing_post['id'], body=body).execute()
            print(f"Post updated successfully: {result['url']}")
            return True
        else:
            print(f"Post '{title}' not found. Creating new post...")
            result = posts.insert(blogId=BLOG_ID, body=body).execute()
            print(f"Post published: {result['url']}")
            return True
    except HttpError as error:
        print(f"An error occurred: {error}")
        return False

def main():
    service = get_service()
    if service:
        publish_post(service)

if __name__ == '__main__':
    main()
