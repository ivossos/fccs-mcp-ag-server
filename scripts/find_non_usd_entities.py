
import csv

with open('data/Ravi_ExportedMetadata_Entity.csv', mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    non_usd = []
    for row in reader:
        currency = row.get('Base Currency', '').strip()
        if currency and currency != 'USD':
            non_usd.append((row['Entity'], currency))

print(f"Found {len(non_usd)} non-USD entities:")
for entity, curr in non_usd:
    print(f"  {entity}: {curr}")



