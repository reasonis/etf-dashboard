import ssl
ssl._create_default_https_context = ssl._create_unverified_context

"""
미국 상장 테마 ETF 리스트 수집기
=================================
소스: financedatabase (pip install financedatabase)
출력: etf_analysis/thematic_etfs.csv          ← 전체 테마 ETF
      etf_analysis/thematic_etf_summary.csv   ← 테마별 집계
      etf_analysis/thematic_etfs_top1.csv     ← 테마별 대표 ETF (AUM 최대 1개)

필터 조건:
  1. 미국 거래소 상장 ETF만
  2. 레버리지/인버스 ETF 제외
  3. 명시적 비미국 단일국가/지역 집중 ETF 제외 (name 기준)
  4. 제외 테마 네거티브 필터 (EXCLUDE_THEMES)
"""

import financedatabase as fd
import pandas as pd
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────
US_EXCHANGES = {'NMS', 'NYQ', 'PCX', 'ASE', 'NGM', 'NCM', 'BTS', 'PNK'}

LEV_KEYWORDS = [
    'leveraged', 'inverse', 'ultra short', 'ultrashort',
    '2x', '3x', '-1x', '-2x', '-3x', '1.5x',
    'bull 2', 'bull 3', 'bear 2', 'bear 3',
    'daily bear', 'daily bull',
]

NONUS_NAME_KEYWORDS = [
    'china', 'chinese', 'japan', 'japanese', 'india', 'indian',
    'korea', 'europe', 'european', 'germany', 'german', 'france', 'french',
    'brazil', 'russia', 'mexico', 'latin america', 'africa', 'middle east',
    'asia', 'asian', 'pacific', 'australia', 'canada', 'taiwan', 'vietnam',
    'indonesia', 'thailand', 'ex-u.s.', 'ex u.s.', 'non-u.s.',
    'acwi', 'eafe', 'msci world', 'ftse developed', 'international equity',
    'emerging market', 'developed market',
]

EXCLUDE_THEMES = [
    'DeFi',
    'ESG',
    'Sustainable',
    'Socially Responsible',
]

THEME_KEYWORDS = {
    "AI":                    ["artificial intelligence", "ai-powered", "ai powered"],
    "Machine Learning":      ["machine learning"],
    "Innovation":            ["innovation", "disruptive technology", "next generation technology"],
    "Cybersecurity":         ["cybersecurity", "cyber security", "information security"],
    "Cloud Computing":       ["cloud computing", "saas"],
    "Big Data":              ["big data"],
    "Data Center":           ["data center"],
    "Semiconductor":         ["semiconductor", "microchip"],
    "Robotics":              ["robotics"],
    "Automation":            ["automation"],
    "Autonomous Vehicle":    ["autonomous vehicle", "autonomous tech", "self-driving"],
    "Electric Vehicle":      ["electric vehicle", " ev "],
    "Battery":               ["battery technology", "lithium battery"],
    "Lithium":               ["lithium"],
    "Clean Energy":          ["clean energy", "renewable energy", "green energy"],
    "Solar":                 ["solar energy"],
    "Wind Energy":           ["wind energy"],
    "Genomics":              ["genomics", "gene editing", "genome"],
    "Biotech":               ["biotech", "biopharma", "biopharmaceutical"],
    "Precision Medicine":    ["precision medicine"],
    "Digital Health":        ["digital health"],
    "Space":                 ["space exploration", "space technology"],
    "Aerospace":             ["aerospace"],
    "Satellite":             ["satellite"],
    "Defense":               ["defense", "national defense"],
    "Military":              ["military"],
    "Fintech":               ["fintech", "financial technology"],
    "Blockchain":            ["blockchain"],
    "Cryptocurrency":        ["cryptocurrency", "digital asset", "crypto"],
    "DeFi":                  ["defi", "decentralized finance"],
    "Gaming":                ["gaming", "video game"],
    "Esports":               ["esports", "e-sports"],
    "Water":                 ["water purification", "water infrastructure", "water technology"],
    "Infrastructure":        ["infrastructure development", "global infrastructure"],
    "5G":                    ["5g network", "5g technology"],
    "IoT":                   ["internet of things", "iot"],
    "Telecom":               ["telecom infrastructure", "telecommunications"],
    "Aging Population":      ["aging population", "longevity"],
    "Healthcare Innovation": ["healthcare innovation"],
    "Cannabis":              ["cannabis", "marijuana", "hemp"],
    "ESG":                   ["esg"],
    "Sustainable":           ["sustainable investing", "sustainability"],
    "Socially Responsible":  ["socially responsible"],
    "E-Commerce":            ["e-commerce", "online retail"],
    "Consumer Trends":       ["consumer trends"],
    "Pet Care":              ["pet care"],
    "Travel & Leisure":      ["travel & leisure", "travel and leisure"],
    "Metaverse":             ["metaverse", "virtual reality", "augmented reality"],
    "Clean Water":           ["clean water"],
    "Nuclear Energy":        ["nuclear energy", "uranium"],
    "Hydrogen":              ["hydrogen energy", "hydrogen fuel"],
}

# ─────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────
def has_any(text, keywords):
    return any(kw in text for kw in keywords)

# ─────────────────────────────────────────────
# 1. 데이터 로드
# ─────────────────────────────────────────────
print("Loading financedatabase ETFs...")
etfs = fd.ETFs()
all_etfs = etfs.select()
print(f"  Total in DB : {len(all_etfs):,}")

us_etfs = all_etfs[all_etfs['exchange'].isin(US_EXCHANGES)].copy()
print(f"  US-listed   : {len(us_etfs):,}")

summary_lower = us_etfs['summary'].fillna('').str.lower()
name_lower    = us_etfs['name'].fillna('').str.lower()

# ─────────────────────────────────────────────
# 2. 레버리지/인버스 제외
# ─────────────────────────────────────────────
lev_mask = (
    summary_lower.apply(lambda x: has_any(x, LEV_KEYWORDS)) |
    name_lower.apply(lambda x: has_any(x, LEV_KEYWORDS)) |
    (us_etfs['category'] == 'Trading')
)
us_etfs = us_etfs[~lev_mask].copy()
print(f"  레버리지/인버스 제외 ({lev_mask.sum()}개) → {len(us_etfs):,}")

# ─────────────────────────────────────────────
# 3. 명시적 비미국 ETF 제외 (name 기준)
# ─────────────────────────────────────────────
name_lower = us_etfs['name'].fillna('').str.lower()
nonus_mask = name_lower.apply(lambda x: has_any(x, NONUS_NAME_KEYWORDS))
us_etfs = us_etfs[~nonus_mask].copy()
print(f"  비미국 제외   ({nonus_mask.sum()}개) → {len(us_etfs):,}")

# ─────────────────────────────────────────────
# 4. 테마 키워드 매칭
# ─────────────────────────────────────────────
summary_lower = us_etfs['summary'].fillna('').str.lower()
name_lower    = us_etfs['name'].fillna('').str.lower()

records = []
for sym, row in us_etfs.iterrows():
    s = summary_lower[sym]
    n = name_lower[sym]
    matched_themes = [
        theme for theme, kws in THEME_KEYWORDS.items()
        if any(kw in s or kw in n for kw in kws)
    ]
    if matched_themes:
        records.append({
            'symbol':   sym,
            'name':     row['name'],
            'themes':   ' | '.join(matched_themes),
            'category': row.get('category', ''),
            'family':   row.get('family', ''),
            'exchange': row.get('exchange', ''),
        })

df = pd.DataFrame(records).drop_duplicates(subset='symbol')

# ─────────────────────────────────────────────
# 4-1. 제외 테마 네거티브 필터
# ─────────────────────────────────────────────
exclude_pattern = '|'.join(EXCLUDE_THEMES)
df = df[~df['themes'].str.contains(exclude_pattern)]
print(f"\n  테마 ETF 최종: {len(df):,}개")

# ─────────────────────────────────────────────
# 5. 테마별 집계
# ─────────────────────────────────────────────
theme_counts = {}
for t_str in df['themes']:
    for t in t_str.split(' | '):
        theme_counts[t] = theme_counts.get(t, 0) + 1

summary_df = pd.DataFrame(
    sorted(theme_counts.items(), key=lambda x: -x[1]),
    columns=['theme', 'etf_count']
)
print(f"\n{summary_df.to_string(index=False)}")

# ─────────────────────────────────────────────
# 6. 저장 (전체)
# ─────────────────────────────────────────────
df.to_csv('etf_analysis/thematic_etfs.csv', index=True, encoding='utf-8-sig')
summary_df.to_csv('etf_analysis/thematic_etf_summary.csv', index=False, encoding='utf-8-sig')
print("\n✓ etf_analysis/thematic_etfs.csv 저장 완료")
print("✓ etf_analysis/thematic_etf_summary.csv 저장 완료")

# ─────────────────────────────────────────────
# 7. 테마별 대표 ETF 선정 (AUM 최대 1개)
#    yfinance에서 totalAssets(=AUM) 조회 후 테마별 1위만 추출
# ─────────────────────────────────────────────
print("\n테마별 대표 ETF 선정 중 (AUM 기준)...")

tickers = df.index.tolist()
aum_map = {}

# 배치 단위로 나눠서 조회 (안정성)
BATCH = 50
for i in range(0, len(tickers), BATCH):
    batch = tickers[i:i+BATCH]
    for sym in batch:
        try:
            info = yf.Ticker(sym).info
            aum  = info.get('totalAssets', None)
            aum_map[sym] = aum
        except Exception:
            aum_map[sym] = None
    print(f"  {min(i+BATCH, len(tickers))}/{len(tickers)} 완료", end='\r')

print()

df['aum'] = df.index.map(aum_map)

# 테마별로 explode → AUM 기준 1위 추출
df_exp = df.copy()
df_exp['theme_single'] = df_exp['themes'].str.split(' | ')
df_exp = df_exp.explode('theme_single')

# EXCLUDE_THEMES는 이미 제거됐지만 explode 후 혹시 남은 것도 방어
df_exp = df_exp[~df_exp['theme_single'].isin(EXCLUDE_THEMES)]

top1 = (
    df_exp
    .sort_values('aum', ascending=False, na_position='last')
    .groupby('theme_single', sort=False)
    .first()
    .reset_index()
    .rename(columns={'theme_single': 'theme'})
    [['theme', 'symbol', 'name', 'aum', 'family', 'category']]
    .sort_values('theme')
)

# 심볼 중복 제거 — 같은 ETF가 여러 테마에 뽑혔을 경우
# AUM 높은 테마 기준으로 1개만 남김
top1 = (
    top1
    .sort_values('aum', ascending=False, na_position='last')
    .drop_duplicates(subset='symbol', keep='first')
    .sort_values('theme')
    .reset_index(drop=True)
)

print(f"\n테마별 대표 ETF ({len(top1)}개):")
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', 40)
pd.set_option('display.width', 120)
print(top1.to_string(index=False))

top1.to_csv('etf_analysis/thematic_etfs_top1.csv', index=False, encoding='utf-8-sig')
print("\n✓ etf_analysis/thematic_etfs_top1.csv 저장 완료")