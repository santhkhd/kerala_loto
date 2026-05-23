with open('scratch/vishu_text.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

output = []
for idx in range(min(len(lines), 200)):
    output.append(f"{idx}: {lines[idx].strip()}")

with open('scratch/vishu_text_start.txt', 'w', encoding='utf-8') as out_f:
    out_f.write('\n'.join(output))

print("Saved first 200 lines of text to scratch/vishu_text_start.txt")
