import os
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional

def load_existing_manifest() -> Dict[str, Any]:
    """Load existing manifest or create empty one."""
    manifest_path = "result_manifest.json"
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading manifest: {e}")
            return {"results": []}
    return {"results": []}

def load_existing_history() -> Dict[str, Any]:
    """Load existing history or create empty one."""
    history_path = "history.json"
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
            return {"draws": []}
    return {"draws": []}

def save_manifest(manifest: Dict[str, Any]):
    """Save manifest to file."""
    try:
        with open("result_manifest.json", 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print("Manifest written successfully")
    except Exception as e:
        print(f"Error saving manifest: {e}")

def save_history(history: Dict[str, Any]):
    """Save history to file."""
    try:
        with open("history.json", 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print("History written successfully")
    except Exception as e:
        print(f"Error saving history: {e}")

def parse_filename(filename: str) -> Optional[Dict[str, str]]:
    """Parse filename to extract lottery code, draw number, and date."""
    # Expected format: XX-XXX-YYYY-MM-DD.json
    pattern = r'^([A-Z]{2,3})-(\d+)-(\d{4}-\d{2}-\d{2})\.json$'
    match = re.match(pattern, filename)
    if match:
        return {
            "lottery_code": match.group(1),
            "draw_number": match.group(2),
            "date": match.group(3)
        }
    return None

def process_manual_uploads():
    """Process manually uploaded JSON files and update manifest/history."""
    note_dir = "note"
    if not os.path.exists(note_dir):
        print("Note directory doesn't exist")
        return
    
    # Load existing data
    manifest = load_existing_manifest()
    history = load_existing_history()
    
    # Get existing filenames in manifest to avoid duplicates
    existing_files = {result["filename"] for result in manifest["results"]}
    
    # Process each JSON file in note directory
    note_files = [f for f in os.listdir(note_dir) if f.endswith('.json') and f != 'latest.json']
    
    new_entries = []
    for filename in note_files:
        if filename in existing_files:
            continue  # Skip existing entries
            
        filepath = os.path.join(note_dir, filename)
        try:
            # Parse filename
            file_info = parse_filename(filename)
            if not file_info:
                print(f"Skipping invalid filename format: {filename}")
                continue
                
            # Load file content
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create manifest entry
            manifest_entry = {
                "filename": filename,
                "lottery_code": file_info["lottery_code"],
                "draw_number": file_info["draw_number"],
                "date": file_info["date"],
                "title": f"{data.get('lottery_name', 'Unknown')} {file_info['lottery_code']}-{file_info['draw_number']}"
            }
            manifest["results"].append(manifest_entry)
            
            # Create history entry
            history_entry = {
                "id": f"{file_info['lottery_code']}-{file_info['draw_number']}",
                "date": file_info["date"],
                "lottery": data.get("lottery_name", "Unknown"),
                "drawNumber": file_info["draw_number"],
                "prizes": []
            }
            
            # Add prize information
            prizes = data.get("prizes", {})
            for prize_key, prize_data in prizes.items():
                history_entry["prizes"].append({
                    "name": prize_data.get("label", prize_key),
                    "amount": prize_data.get("amount", 0),
                    "winners": len(prize_data.get("winners", []))
                })
            
            history["draws"].append(history_entry)
            new_entries.append(filename)
            print(f"Processed: {filename}")
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    if new_entries:
        # Sort manifest by date (newest first)
        manifest["results"].sort(key=lambda x: x["date"], reverse=True)
        
        # Sort history by date (newest first)
        history["draws"].sort(key=lambda x: x["date"], reverse=True)
        
        # Save updated files
        save_manifest(manifest)
        save_history(history)
        
        print(f"Added {len(new_entries)} new entries:")
        for entry in new_entries:
            print(f"  - {entry}")
    else:
        print("No new files to process")

def update_latest_result():
    """Update latest.json with the most recent result."""
    note_dir = "note"
    if not os.path.exists(note_dir):
        print("Note directory doesn't exist")
        return
    
    # Find the most recent file
    note_files = [f for f in os.listdir(note_dir) if f.endswith('.json') and f != 'latest.json']
    if not note_files:
        print("No result files found")
        return
    
    # Parse dates and sort
    file_dates = []
    for filename in note_files:
        file_info = parse_filename(filename)
        if file_info:
            file_dates.append((filename, file_info["date"]))
    
    if not file_dates:
        print("No valid files found")
        return
    
    # Sort by date and get the most recent
    file_dates.sort(key=lambda x: x[1], reverse=True)
    latest_filename = file_dates[0][0]
    
    # Copy the latest file to latest.json
    source_path = os.path.join(note_dir, latest_filename)
    dest_path = os.path.join(note_dir, "latest.json")
    
    try:
        with open(source_path, 'r', encoding='utf-8') as src:
            data = json.load(src)
        
        with open(dest_path, 'w', encoding='utf-8') as dst:
            json.dump(data, dst, indent=2, ensure_ascii=False)
        
        print(f"Updated latest.json with {latest_filename}")
    except Exception as e:
        print(f"Error updating latest.json: {e}")

if __name__ == "__main__":
    print("Processing manually uploaded JSON files...")
    
    # Process new files and update manifest/history
    process_manual_uploads()
    
    # Update latest.json
    update_latest_result()
    
    print("Processing complete!")