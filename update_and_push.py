import subprocess
import os
import logging
import sys
import time
from datetime import datetime
import pytz

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_and_push.log"),
        logging.StreamHandler()
    ]
)

# Set Indian timezone
IST = pytz.timezone('Asia/Kolkata')

def run_command(command, description):
    """Run a system command and log the output"""
    logging.info(f"Starting: {description}")
    try:
        # Check if the command exists (especially for node which caused issues)
        result = subprocess.run(command, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            logging.info(f"Success: {description}")
            if result.stdout:
                logging.info(f"Output: {result.stdout.strip()}")
            return True
        else:
            logging.error(f"Error in {description}: {result.stderr}")
            if "not found" in result.stderr or "No such file" in result.stderr:
                logging.error(f"Is {command[0]} installed and in PATH?")
            return False
    except Exception as e:
        logging.error(f"Exception during {description}: {e}")
        return False

def commit_and_push():
    """Commit and push changes to GitHub"""
    logging.info("Checking for changes to commit...")
    
    # Check if there are any changes
    status = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
    if not status.stdout.strip():
        logging.info("No changes to commit (result likely not available yet).")
        return False
        
    # Git identity check
    subprocess.run(['git', 'config', '--global', 'user.name', 'Lottery Bot'], check=False)
    subprocess.run(['git', 'config', '--global', 'user.email', 'bot@lottery.com'], check=False)

    # Add, Commit, Push
    if run_command(['git', 'add', '.'], "Git Add"):
        commit_msg = f"Auto-update: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST"
        if run_command(['git', 'commit', '-m', commit_msg], "Git Commit"):
            # Push to both main and master to ensure visibility and website updates
            logging.info("Pushing to multiple branches for redundancy...")
            success_master = run_command(['git', 'push', 'origin', 'HEAD:master'], "Git Push to Origin (Master)")
            success_main = run_command(['git', 'push', 'origin', 'HEAD:main', '--force'], "Git Push to Origin (Main)")
            
            # For the loto mirror
            success_loto = run_command(['git', 'push', 'loto', 'HEAD:master', '--force'], "Git Push to Loto Mirror (Master)")
            
            return success_master or success_main or success_loto
    return False

def main():
    logging.info("=== Starting Kerala Lottery Update Task ===")
    
    # 0. Sync with GitHub first
    # This cleans up the repo and ensures we have the latest code from master
    run_command(['git', 'fetch', 'origin'], "Git Fetch")
    run_command(['git', 'reset', '--hard', 'origin/master'], "Git Sync (Reset to Remote Master)")
    
    # 1. Run the scraper (using the more robust updateloto.py)
    # This uses fallback proxies which are useful on restricted environments like PythonAnywhere
    if not run_command([sys.executable, 'updateloto.py'], "Lottery Scraper"):
        logging.warning("Scraper failed or had warnings, proceeding anyway...")

    # 2. Generate Manifest (Using Python version to remove Node.js dependency)
    run_command([sys.executable, 'generate_manifest.py'], "Manifest Generation")

    # 3. Generate History (Using Python version to remove Node.js dependency)
    run_command([sys.executable, 'generate_history.py'], "History Generation")

    # 4. Generate PDF Links (Using Python version to remove Node.js dependency)
    run_command([sys.executable, 'generate_pdf_links.py'], "PDF Link Generation")

    # 5. Push to GitHub
    if commit_and_push():
        logging.info("Update and push completed successfully!")
        return True
    else:
        logging.error("Failed to update GitHub.")
        return False

if __name__ == "__main__":
    # To run this up to 7 times automatically:
    # It will stop as soon as it successfully pushes a new result.
    runs = 7
    delay_minutes = 15
    
    for i in range(runs):
        logging.info(f"--- Starting Run {i+1} of {runs} ---")
        success = main()
        
        if success:
            logging.info("Result found and pushed. Stopping further runs for today.")
            break
            
        if i < runs - 1:
            logging.info(f"Waiting {delay_minutes} minutes before next check...")
            time.sleep(delay_minutes * 60)
    
    logging.info("=== Daily update task finished. ===")
