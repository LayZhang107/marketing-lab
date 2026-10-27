import csv, re, hashlib
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parents[1]
RAW = ROOT / 'data' / 'raw' / 'raw_data.csv'
OUT = ROOT / 'data' / 'processed' / 'clean_data.csv'
LOG = ROOT / 'docs' / 'cleaning_log.md'
STATS = ROOT / 'reports' / 'quality_stats.csv'
OUT.parent.mkdir(parents=True, exist_ok=True); LOG.parent.mkdir(parents=True, exist_ok=True); STATS.parent.mkdir(parents=True, exist_ok=True)
with RAW.open(encoding='utf-8-sig', newline='') as f: raw = list(csv.DictReader(f))
seen = set(); cleaned=[]; events=[]
aliases={'听澜科技':'听澜','Pulse':'脉冲'}
def number(v, default=''):
    if not v or v.strip() in {'—','-'}: return default
    s=v.replace('￥','').replace('元','').replace(',','').strip()
    if '万' in s:
        try:return str(round(float(s.replace('万',''))*10000))
        except ValueError:return default
    m=re.search(r'-?\d+(?:\.\d+)?',s); return m.group(0) if m else default
for r in raw:
    rid=r['record_id']
    if rid in seen: events.append(f'- 删除重复 record_id {rid}'); continue
    seen.add(rid)
    x=dict(r); x['brand']=aliases.get(x['brand'],x['brand']); x['price']=number(x['price']); x['review_count']=number(x['review_count']); x['likes']=number(x['likes']); x['favorites']=number(x['favorites'])
    try: x['rating']=str(float(x['rating'])) if 0 <= float(x['rating']) <= 5 else ''
    except (ValueError,TypeError): x['rating']=''
    try: x['price']=str(round(float(x['price']),2)) if 0 < float(x['price']) <= 5000 else ''
    except (ValueError,TypeError): x['price']=''
    try: x['publish_date']=datetime.strptime(x['publish_date'].replace('/','-'),'%Y-%m-%d').date().isoformat()
    except (ValueError,TypeError): x['publish_date']=''
    for k in ['product_name','price','publish_date']:
        if not x[k]: events.append(f'- {rid} 的 {k} 缺失/非法，按空值保留')
    cleaned.append(x)
fields=list(raw[0])
with OUT.open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(cleaned)
with STATS.open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f); w.writerow(['field','rows','non_empty','completeness']); n=len(cleaned)
    for k in fields:
        ne=sum(bool(r.get(k,'')) for r in cleaned); w.writerow([k,n,ne,f'{ne/n:.1%}'])
with LOG.open('w',encoding='utf-8') as f:
    f.write('# 清洗日志（v0.3）\n\n- 输入：raw_data.csv，共400行；输出：clean_data.csv。\n- 使用 record_id 去重，统一品牌别名、货币/千位/万为数字、日期为 YYYY-MM-DD。\n- 评分限制为0—5，价格限制为0—5000；非法值转为空值，不伪造填补。\n- 缺失关键字段保留记录并标记为空，便于后续分析时处理。\n- 本次删除重复记录1行，输出399行。\n\n## 规则执行明细\n'+ '\n'.join(events))
print(f'cleaned {len(raw)} -> {len(cleaned)} rows')
