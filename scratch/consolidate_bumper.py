import json
import os

def consolidate():
    br_path = 'note/BR-109-2026-05-23.json'
    vb_path = 'note/VB-May 23, 2026-2026-05-23.json'
    out_path = 'note/VB-109-2026-05-23.json'

    with open(br_path, 'r', encoding='utf-8') as f:
        br_data = json.load(f)
    
    with open(vb_path, 'r', encoding='utf-8') as f:
        vb_data = json.load(f)

    # Consolidate: use vb_data prizes and download link, but update name and draw number
    consolidated = vb_data.copy()
    consolidated['lottery_name'] = 'VISHU BUMPER'
    consolidated['draw_number'] = '109'
    consolidated['draw_code'] = 'VB-109'
    consolidated['venue'] = br_data.get('venue') or vb_data.get('venue') or ''

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(consolidated, f, indent=2, ensure_ascii=False)
    
    # Delete old files
    if os.path.exists(br_path):
        os.remove(br_path)
    if os.path.exists(vb_path):
        os.remove(vb_path)

    # Consolidate result_manifest.json
    manifest_path = 'result_manifest.json'
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    # Filter out duplicate entries for 2026-05-23
    new_manifest = [x for x in manifest if x.get('date') != '2026-05-23']
    
    # Add consolidated entry at the top
    consolidated_entry = {
        "code": "VB",
        "draw_number": "109",
        "date": "2026-05-23",
        "filename": "VB-109-2026-05-23.json"
    }
    new_manifest.insert(0, consolidated_entry)

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(new_manifest, f, indent=2, ensure_ascii=False)

    print("Consolidation complete!")

if __name__ == '__main__':
    consolidate()
