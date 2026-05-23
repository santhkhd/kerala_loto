with open('scratch/today_live_text.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

output = []
for idx in range(min(len(lines), 80)):
    output.append(f"{idx}: {lines[idx].strip()}")

with open('scratch/today_live_text_start.txt', 'w', encoding='utf-8') as out_f:
    out_f.write('\n'.join(output))

print("Saved first 80 lines to scratch/today_live_text_start.txt")
