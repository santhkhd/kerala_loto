# Kerala Lottery Results Automation

This project automatically fetches the latest Kerala lottery results 5 times daily at specific times to ensure up-to-date information.

## Automated Schedule

The scheduler runs at these specific times daily (IST):
- 3:15 PM
- 3:30 PM
- 3:45 PM
- 4:15 PM
- 4:30 PM

These times were chosen to capture the latest lottery results as they are typically published around 3:00 PM IST.

## How It Works

1. The [auto_scheduler.py](auto_scheduler.py) script uses the `schedule` library to run at the specified times
2. At each scheduled time, it executes [updateloto.py](updateloto.py) which:
   - Scrapes the latest lottery results from https://www.kllotteryresult.com/
   - Processes and saves the results as JSON files in the [note/](note/) directory
   - Updates the [note/latest.json](note/latest.json) file with the most recent results
3. After successful scraping, it automatically runs [generate-history.js](generate-history.js) to update the [history.json](history.json) file

## Setup Instructions

### Prerequisites

1. Python 3.7 or higher
2. Node.js 12 or higher
3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Install required Node.js packages:
   ```bash
   npm install
   ```

### Running the Scheduler

To start the automated scheduler:

```bash
python auto_scheduler.py
```

The scheduler will:
- Run once immediately when started
- Then run at the specified times each day
- Log all activities to both console and [scheduler.log](scheduler.log)

### Manual Execution

To manually fetch the latest results at any time:

```bash
python updateloto.py
```

To manually regenerate the history file:

```bash
node generate-history.js
```

## GitHub Integration

To automatically push updates to GitHub:

1. Set up a GitHub personal access token
2. Set the `GITHUB_TOKEN` environment variable:
   ```bash
   export GITHUB_TOKEN=your_github_token_here
   ```
   
When the `GITHUB_TOKEN` is set, the scheduler will automatically commit and push any new results to the repository.

## File Structure

- [auto_scheduler.py](auto_scheduler.py) - Main scheduler that runs at specific times
- [updateloto.py](updateloto.py) - Scrapes and processes lottery results
- [generate-history.js](generate-history.js) - Generates history.json from individual result files
- [note/](note/) - Directory containing individual lottery result JSON files
- [history.json](history.json) - Consolidated history of all lottery results
- [scheduler.log](scheduler.log) - Log file with scheduler activities

## Troubleshooting

If you encounter issues:

1. Check the [scheduler.log](scheduler.log) file for error messages
2. Ensure all dependencies are installed (`pip install -r requirements.txt` and `npm install`)
3. Verify internet connectivity
4. Check that the source website is accessible: https://www.kllotteryresult.com/

If the scheduler stops running, simply restart it with `python auto_scheduler.py`.