with open('scratch/vishu_text.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if '1st Prize' in line or '2nd Prize' in line or 'Consolation Prize' in line or 'VB 135452' in line:
        print(f"--- MATCH AT LINE {idx} ---")
        start = max(0, idx - 5)
        end = min(len(lines), idx + 15)
        for i in range(start, end):
            print(f"{i}: {lines[i].strip()}")
