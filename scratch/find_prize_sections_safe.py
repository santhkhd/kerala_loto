import sys

with open('scratch/vishu_text.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

output = []
for idx, line in enumerate(lines):
    if '1st Prize' in line or '2nd Prize' in line or 'Consolation Prize' in line or 'VB 135452' in line or 'VB 135452' in line:
        output.append(f"--- MATCH AT LINE {idx} ---")
        start = max(0, idx - 5)
        end = min(len(lines), idx + 25)
        for i in range(start, end):
            output.append(f"{i}: {lines[i].strip()}")

with open('scratch/prize_sections_found.txt', 'w', encoding='utf-8') as out_f:
    out_f.write('\n'.join(output))

print("Results saved to scratch/prize_sections_found.txt")
