import csv, random
from datetime import date, timedelta
from pathlib import Path

SEED = 20261027
random.seed(SEED)
ROOT = Path(__file__).parents[1]
OUT = ROOT / 'data' / 'raw' / 'raw_data.csv'
OUT.parent.mkdir(parents=True, exist_ok=True)

brands = [('声界', '声界'), ('听澜', '听澜科技'), ('脉冲', 'Pulse'), ('云音', '云音')]
platforms = ['星河商城', '云集平台', '微光商城']
fields = ['record_id','product_name','brand','category','platform','price','rating','review_count','publish_date','likes','favorites']
rows = []
start = date(2025, 1, 1)
for i in range(400):
    b, alias = brands[i // 100]
    product = f'{b} Aero {i % 5 + 1}'
    price = round(random.uniform(99, 599), 2)
    rating = round(random.uniform(3.2, 4.9), 1)
    reviews = random.randint(20, 9800)
    d = start + timedelta(days=random.randint(0, 620))
    row = [f'R{i+1:04d}', product, b, '蓝牙耳机', random.choice(platforms), f'{price:.2f}元', rating, f'{reviews:,}', d.isoformat(), random.randint(0, 30000), random.randint(0, 12000)]
    rows.append(row)

# Deliberate defects for the teaching exercise.
rows[7][1] = ''
rows[18][5] = ''
rows[29][8] = ''
rows[41][2] = '听澜科技'
rows[52][2] = 'Pulse'
rows[63][5] = '￥299'
rows[74][8] = '2025/03/15'
rows[85][6] = '70'
rows[96][5] = '-20'
rows[107][9] = '1.2万'
rows[118][10] = '—'
rows[129][0] = 'R0130'
rows[149] = rows[148].copy()

with OUT.open('w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(fields); w.writerows(rows)
print(f'generated {len(rows)} rows -> {OUT}')
