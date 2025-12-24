
with open('data/actual_monthly_data_jan_jun_fy25.csv', mode='r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'CTA' in line or 'Translation' in line:
            print(f"{i}: {line.strip()}")



