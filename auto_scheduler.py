import schedule
import time
import subprocess
import pytz
from datetime import datetime, time as dt_time
import threading
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)

# Set Indian timezone
IST = pytz.timezone('Asia/Kolkata')

def run_lottery_scraper():
    """Run the lottery scraper"""
    try:
        logging.info(f"Running lottery scraper at {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST")
        result = subprocess.run(['python', 'updateloto.py'], capture_output=True, text=True)
        if result.returncode == 0:
            logging.info("Lottery scraper completed successfully")
            if result.stdout:
                logging.info(f"Output: {result.stdout}")
        else:
            logging.error(f"Error running lottery scraper: {result.stderr}")
    except Exception as e:
        logging.error(f"Exception occurred: {e}")

def is_within_time_range():
    """Check if current time is between 2:45 PM and 5:30 PM IST (lottery result publishing time)"""
    now = datetime.now(IST)
    start_time = dt_time(14, 45)  # 2:45 PM
    end_time = dt_time(17, 30)    # 5:30 PM
    current_time = now.time()
    
    return start_time <= current_time <= end_time

def scheduled_task():
    """Task that runs every 15 minutes but only executes during specified hours"""
    current_time = datetime.now(IST).strftime('%H:%M:%S')
    logging.info(f"Scheduler check at {current_time} IST")
    
    if is_within_time_range():
        logging.info("Within scheduled time range - running lottery scraper")
        run_lottery_scraper()
    else:
        logging.info(f"Current time {current_time} IST is outside scheduled range (14:45-17:30)")

def run_scheduler():
    """Run the scheduler in a separate thread"""
    # Schedule the task to run every 15 minutes during the day
    schedule.every(15).minutes.do(scheduled_task)
    
    logging.info("Scheduler started - will check every 15 minutes")
    logging.info("Active time: 2:45 PM to 5:30 PM IST daily")
    logging.info("Press Ctrl+C to stop the scheduler")
    
    # Run one initial check
    scheduled_task()
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    # Check if GitHub token is set
    if not os.environ.get('GITHUB_TOKEN'):
        logging.warning("GITHUB_TOKEN not set. Auto-push to GitHub will not work.")
        logging.info("Please set GITHUB_TOKEN in your environment variables for automatic GitHub pushes.")
    
    try:
        logging.info("Starting Kerala lottery result scheduler...")
        logging.info(f"Current time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST")
        
        # Start the scheduler
        run_scheduler()
    except KeyboardInterrupt:
        logging.info("Scheduler stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
