with open('update_and_push.log', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for line in lines[-150:]:
    print(line.strip())
