with open('scratch/today_live_text.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

output = []
for idx in range(max(0, 950), min(len(lines), 1150)):
    output.append(f"{idx}: {lines[idx].strip()}")

with open('scratch/today_live_text_end.txt', 'w', encoding='utf-8') as out_f:
    out_f.write('\n'.join(output))

print("Saved lines 950-1150 to scratch/today_live_text_end.txt")
