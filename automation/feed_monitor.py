import os
import json
import re
import base64
import requests
import feedparser
from datetime import datetime

# CONFIGURATION
# Set these in your environment variables for security
ONESIGNAL_APP_ID = os.getenv('ONESIGNAL_APP_ID', 'YOUR_APP_ID_HERE')
ONESIGNAL_REST_KEY = os.getenv('ONESIGNAL_REST_KEY', 'YOUR_REST_KEY_HERE')

# PATHS
CONFIG_FILE = 'app/src/main/java/com/app/webdroid/Config.java'
ASSETS_DIR = 'app/src/main/assets'
STATE_FILE = 'automation/last_seen.json'

def send_onesignal_notification(title, message, link=None, title_ml=None, message_ml=None):
    """Sends a push notification via OneSignal REST API with optional Malayalam support"""
    url = "https://onesignal.com/api/v1/notifications"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Basic {ONESIGNAL_REST_KEY}"
    }
    
    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["All"],
        "headings": {
            "en": title,
            "ml": title_ml if title_ml else title
        },
        "contents": {
            "en": message,
            "ml": message_ml if message_ml else message
        }
    }
    
    if link:
        payload["url"] = link  # Device opens this link when clicked

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        print(f"Notification Status: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending notification: {e}")

def get_latest_item(feed_url):
    """Fetches the latest item from an RSS feed"""
    try:
        # Fetch with timeout to prevent hanging on hundreds of URLs
        resp = requests.get(feed_url, timeout=10)
        feed = feedparser.parse(resp.content)
        if feed.entries:
            latest = feed.entries[0]
            return {
                'id': latest.get('id', latest.get('link')),
                'title': latest.get('title', 'New Content'),
                'link': latest.get('link')
            }
    except Exception as e:
        pass # Silently fail on bad feeds to avoid spamming the log
    return None

def get_remote_json_url():
    """Reads Config.java, parses the ACCESS_KEY, and decodes it to get the remote config URL."""
    if not os.path.exists(CONFIG_FILE):
        print(f"Config.java not found at: {CONFIG_FILE}")
        return None
        
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Match public static final String ACCESS_KEY = "value";
        match = re.search(r'ACCESS_KEY\s*=\s*["\']([^"\']+)["\']', content)
        if not match:
            print("ACCESS_KEY not found in Config.java")
            return None
            
        access_key = match.group(1)
        if not access_key or 'XXXXX' in access_key:
            print("ACCESS_KEY is empty or not configured")
            return None
            
        # If the access key is a direct HTTP/HTTPS URL, return it directly
        if access_key.startswith('http://') or access_key.startswith('https://'):
            print(f"Using direct remote URL: {access_key}")
            return access_key
            
        # The key is triple Base64-encoded
        decoded = access_key
        for _ in range(3):
            # Pad key if needed (standard Base64 requirement)
            missing_padding = len(decoded) % 4
            if missing_padding:
                decoded += '=' * (4 - missing_padding)
            decoded = base64.b64decode(decoded).decode('utf-8')
            
        # Split by _applicationId_
        parts = decoded.split('_applicationId_')
        remote_url = parts[0]
        print(f"Successfully decoded remote URL: {remote_url}")
        return remote_url
    except Exception as e:
        print(f"Error decoding ACCESS_KEY: {e}")
        return None

def check_and_send_pre_draw_reminder(last_seen):
    """Sends a daily pre-draw reminder notification 15 minutes before the draw starts (around 2:45 PM IST / 9:15 AM UTC)"""
    try:
        from datetime import timezone
        now_utc = datetime.now(timezone.utc)
        if now_utc.hour == 9 and 10 <= now_utc.minute <= 27:
            today_str = now_utc.strftime('%Y-%m-%d')
            # Check if we already sent the reminder today to avoid duplicates
            if last_seen.get('last_reminder_date') != today_str:
                print("Time detected for pre-draw reminder. Sending attractive reminder notifications...")
                title_en = "Are you today's lucky winner? 🌟"
                msg_en = "Kerala Lottery results start in 15 minutes! Open the app now to be ready. 🔔"
                
                title_ml = "ഇന്നത്തെ ഭാഗ്യശാലി നിങ്ങളാണോ? 🌟"
                msg_ml = "കേരള ലോട്ടറി ഫലങ്ങൾ 15 മിനിറ്റിനുള്ളിൽ വരുന്നു! ഫലങ്ങൾ അറിയാൻ ഇപ്പോൾ തന്നെ ആപ്പ് തുറക്കൂ. 🔔"
                
                # Send to OneSignal (links to home page)
                send_onesignal_notification(
                    title=title_en,
                    message=msg_en,
                    link="https://santhkhd.github.io/kerala_loto/index.html",
                    title_ml=title_ml,
                    message_ml=msg_ml
                )
                
                # Record that we sent it today
                last_seen['last_reminder_date'] = today_str
    except Exception as e:
        print(f"Error checking pre-draw reminder: {e}")

def check_and_send_lucky_number_reminder(last_seen):
    """Sends a recurring 'lucky or dream number' reminder notification every 2 hours during active IST hours"""
    try:
        from datetime import timezone
        now_utc = datetime.now(timezone.utc)
        
        # Target UTC hours corresponding to 8 AM, 10 AM, 12 PM, 2 PM, 6 PM, 8 PM, 10 PM IST
        target_hours = [2, 4, 6, 8, 12, 14, 16]
        
        # We allow a wider minute range to accommodate GitHub Action startup delays
        if now_utc.hour in target_hours and 25 <= now_utc.minute <= 45:
            today_str = now_utc.strftime('%Y-%m-%d')
            state_key = f"{today_str}_{now_utc.hour}"
            
            if last_seen.get('last_lucky_notification') != state_key:
                print(f"Active slot for 2-hour lucky number notification (Hour {now_utc.hour} UTC). Sending...")
                
                # Dynamic templates to keep notifications engaging
                templates = [
                    {
                        "en_title": "What was your dream last night? 💭",
                        "en_msg": "Find your lucky lottery numbers based on your dream inside the app! 🔮",
                        "ml_title": "ഇന്നത്തെ സ്വപ്നം ഫലിക്കുമോ? 💭",
                        "ml_msg": "നിങ്ങളുടെ സ്വപ്നത്തെ അടിസ്ഥാനമാക്കിയുള്ള ഭാഗ്യ നമ്പറുകൾ ഇപ്പോൾ തന്നെ ആപ്പിൽ കണ്ടെത്തൂ! 🔮"
                    },
                    {
                        "en_title": "Feeling lucky today? 🍀",
                        "en_msg": "Generate your lucky numbers and check if today is your day! 🌟",
                        "ml_title": "ഇന്ന് ഭാഗ്യം നിങ്ങളുടെ കൂടെയുണ്ടോ? 🍀",
                        "ml_msg": "നിങ്ങളുടെ ഭാഗ്യ നമ്പറുകൾ തിരഞ്ഞെടുത്ത് ഇന്നത്തെ വിജയിയാകൂ! 🌟"
                    },
                    {
                        "en_title": "Your dream could be worth millions! 💰",
                        "en_msg": "Convert your dreams into lucky lottery numbers now! 🚀",
                        "ml_title": "സ്വപ്നങ്ങൾക്ക് ലക്ഷങ്ങളുടെ വിലയുണ്ട്! 💰",
                        "ml_msg": "നിങ്ങളുടെ സ്വപ്നങ്ങളെ ഭാഗ്യ നമ്പറുകളാക്കി ഇപ്പോൾ തന്നെ മാറ്റൂ! 🚀"
                    },
                    {
                        "en_title": "Select your lucky numbers! ✨",
                        "en_msg": "Is today your lucky day? Tap to select your special numbers now! 🎰",
                        "ml_title": "ഭാഗ്യ നമ്പറുകൾ തിരഞ്ഞെടുക്കൂ! ✨",
                        "ml_msg": "ഇന്ന് നിങ്ങളുടെ ഭാഗ്യദിനമാണോ? നിങ്ങളുടെ പ്രത്യേക നമ്പറുകൾ ഇപ്പോൾ തന്നെ കണ്ടെത്തൂ! 🎰"
                    }
                ]
                
                # Pick a template deterministically based on the hour to ensure variation
                template_idx = now_utc.hour % len(templates)
                selected = templates[template_idx]
                
                send_onesignal_notification(
                    title=selected["en_title"],
                    message=selected["en_msg"],
                    link="https://santhkhd.github.io/kerala_loto/index.html",
                    title_ml=selected["ml_title"],
                    message_ml=selected["ml_msg"]
                )
                
                last_seen['last_lucky_notification'] = state_key
    except Exception as e:
        print(f"Error checking lucky number reminder: {e}")

def monitor():
    # Load previous state
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            last_seen = json.load(f)
    else:
        last_seen = {}

    # Check and send the pre-draw daily app-open reminder
    check_and_send_pre_draw_reminder(last_seen)

    # Check and send the 2-hour lucky/dream number reminder
    check_and_send_lucky_number_reminder(last_seen)

    feeds_to_check = []

    # 1. Try to fetch feeds from remote JSON URL decoded from Config.java
    remote_url = get_remote_json_url()
    remote_success = False
    if remote_url:
        try:
            print(f"Fetching remote configuration from: {remote_url}")
            resp = requests.get(remote_url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                remote_success = True
                
                # Check for menus in remote configuration
                if isinstance(data, dict) and 'menus' in data:
                    menus = data['menus']
                    print(f"Found {len(menus)} menus in remote configuration.")
                    for item in menus:
                        name = item.get('name') or item.get('title')
                        if not name:
                            continue
                        
                        # Extract feeds from url/url_dark or specific provider keys
                        # Support url, rss_url, url_dark, etc.
                        for key in ['url', 'url_dark', 'rss_url']:
                            feed_url = item.get(key)
                            if feed_url and (feed_url.startswith('http://') or feed_url.startswith('https://')):
                                feeds_to_check.append({
                                    'name': name,
                                    'url': feed_url
                                })
            else:
                print(f"Failed to fetch remote config: HTTP {resp.status_code}")
        except Exception as e:
            print(f"Error checking remote feeds: {e}")

    # 2. Fallback to scanning local assets directory if remote fetch failed or returned no feeds
    if not remote_success or not feeds_to_check:
        print("Using local assets directory fallback...")
        if os.path.exists(ASSETS_DIR):
            for filename in os.listdir(ASSETS_DIR):
                if filename.endswith('.json'):
                    path = os.path.join(ASSETS_DIR, filename)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                            # Handle array-based feed lists (like news_channels.json, top_news_rss.json)
                            if isinstance(data, list):
                                for item in data:
                                    name = item.get('name') or item.get('title')
                                    if not name or item.get('provider') == 'webview':
                                        continue
                                        
                                    feed_url = None
                                    if item.get('provider') == 'rss' and 'arguments' in item and len(item['arguments']) > 0:
                                        feed_url = item['arguments'][0]
                                    elif 'rss_url' in item:
                                        feed_url = item['rss_url']
                                    elif 'url' in item:
                                        feed_url = item['url']
                                        
                                    if feed_url:
                                        feeds_to_check.append({
                                            'name': name,
                                            'url': feed_url
                                        })
                            
                            # Handle config.json structure
                            elif isinstance(data, dict):
                                if 'rss_news' in data:
                                    for item in data['rss_news']:
                                        feeds_to_check.append({
                                            'name': item.get('title', 'RSS News'),
                                            'url': item.get('url')
                                        })
                                if 'youtube_channels' in data:
                                    for item in data['youtube_channels']:
                                        channel_id = item.get('channel_id')
                                        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
                                        feeds_to_check.append({
                                            'name': item.get('name', 'YouTube Channel'),
                                            'url': rss_url
                                        })
                    except Exception as e:
                        print(f"Error reading local file {filename}: {e}")
        else:
            print(f"Local assets directory not found: {ASSETS_DIR}")

    # Remove duplicate urls to avoid redundant checks
    seen_urls = set()
    unique_feeds = []
    for feed in feeds_to_check:
        url = feed['url']
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_feeds.append(feed)
    feeds_to_check = unique_feeds

    # 3. Check each feed for updates
    print(f"Checking {len(feeds_to_check)} unique feeds at {datetime.now()}...")
    
    new_state = {}
    notifications_sent = 0

    for feed in feeds_to_check:
        url = feed['url']
        if not url: continue
        
        latest = get_latest_item(url)
        if latest:
            new_state[url] = latest['id']
            
            # If we've seen this feed before but the ID is different
            if url in last_seen and last_seen[url] != latest['id']:
                print(f"New content found in {feed['name']}: {latest['title']}")
                
                # LIMIT TO 2 NOTIFICATIONS PER RUN
                if notifications_sent < 2:
                    title_en = f"New from {feed['name']}! 🔔"
                    title_ml = f"{feed['name']}-ൽ നിന്നുള്ള പുതിയ അപ്‌ഡേറ്റ്! 🔔"
                    
                    send_onesignal_notification(
                        title=title_en,
                        message=latest['title'],
                        link=latest['link'],
                        title_ml=title_ml,
                        message_ml=latest['title']
                    )
                    notifications_sent += 1
                else:
                    print(f"Skipping notification for {feed['name']} - Limit reached for this hour.")

            elif url not in last_seen:
                print(f"Tracking new feed: {feed['name']}")
    
    # Save the updated state
    # Merge existing state to not lose feeds that might have failed this time
    last_seen.update(new_state)
    with open(STATE_FILE, 'w') as f:
        json.dump(last_seen, f, indent=4)

    print(f"Done. Sent {notifications_sent} notifications.")

if __name__ == "__main__":
    monitor()

