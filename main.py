import json
import pandas as pd

# --- 設定（定数） ---
DATA_FILE = "default-cards-20260516091059.json"
MIN_GAP_DAYS = 10000
TOP_N_ITEMS = 30
# --------------------

# Scryfallのバルクデータを読み込み
print("データを読み込み中...")
with open(DATA_FILE, "r", encoding="utf-8") as f:
    cards = json.load(f)

card_prints = []

print("データを抽出中...")
for card in cards:
    # デジタル専用セット（MTGO/アリーナ限定）を除外
    if card.get("digital"):
        continue

    # type_lineがNoneになる極稀なケースへの安全対策
    type_line = card.get("type_line") or ""
    
    # トーナメントで使用できないカードタイプを包括的に除外
    if any(t in type_line for t in ["Basic Land", "Token", "Conspiracy", "Attraction"]):
        continue
        
    # トーナメントのデッキに組み込めない特殊レイアウトやセットタイプを除外
    invalid_layouts = {"token", "double_faced_token", "emblem", "art_series", "planar", "scheme", "vanguard", "hero"}
    if card.get("layout") in invalid_layouts or card.get("set_type") in {"token", "minigame", "memorabilia"}:
        continue
        
    # 銀枠、金枠、どんぐりスタンプなど非公式カードの除外
    if card.get("border_color") in {"silver", "gold"} or card.get("security_stamp") == "acorn":
        continue

    # 大判カード、提示用統率者カード（thick）、プレイテストカードなどを除外
    promo_types = set(card.get("promo_types", []))
    if card.get("oversized") or {"playtest", "thick"} & promo_types:
        continue

    oracle_id = card.get("oracle_id")
    name = card.get("name")
    set_code = card.get("set")
    released_at = card.get("released_at")
    
    if oracle_id and released_at:
        card_prints.append({
            "oracle_id": oracle_id,
            "name": name,
            "set": set_code,
            "released_at": released_at
        })

# DataFrameに変換
df = pd.DataFrame(card_prints)
df['released_at'] = pd.to_datetime(df['released_at'])

# 同一カードが同じ日（または同じセット）に複数収録されている場合の重複を排除し、純粋な「日付ごとのリリース」にする
df = df.drop_duplicates(subset=['oracle_id', 'released_at'])

# 空白期間の計算（Pandasのベクトル演算による高速化）
print("空白期間を計算中...")

# 発売日順にソート（shiftを正しく機能させるため必須）
df = df.sort_values(by=['oracle_id', 'released_at'])

# 各カードごとに前回（1つ前）のリリース日とセットを取得
df['prev_released_at'] = df.groupby('oracle_id')['released_at'].shift(1)
df['prev_set'] = df.groupby('oracle_id')['set'].shift(1)

# 日数差を計算（初版や再録がないカードはNaNになる）
df['gap_days'] = (df['released_at'] - df['prev_released_at']).dt.days

# gap_daysがNaNの行（再録ではない行）を除外
df = df.dropna(subset=['gap_days'])
df['gap_days'] = df['gap_days'].astype(int)

# 各カードにおける最大の空白期間を持つ行（インデックス）を取得
max_gap_idx = df.groupby('oracle_id')['gap_days'].idxmax()
result_df = df.loc[max_gap_idx].copy()

# 出力用に列を整形
result_df['prev_set'] = result_df['prev_set'].str.upper()
result_df['next_set'] = result_df['set'].str.upper()
result_df['prev_date'] = result_df['prev_released_at'].dt.strftime('%Y-%m-%d')
result_df['next_date'] = result_df['released_at'].dt.strftime('%Y-%m-%d')

# 必要な列だけ抽出し、日数降順でソート（同じ日数の場合は名前順）
result_df = result_df[['name', 'prev_set', 'next_set', 'prev_date', 'next_date', 'gap_days']]
result_df = result_df.sort_values(by=["gap_days", "name"], ascending=[False, True])

# 指定された日数以上のカード、または上位N件を表示
print("\n=== 再録までの空白期間が長かったカード ===")
over_threshold = result_df[result_df["gap_days"] >= MIN_GAP_DAYS]

if not over_threshold.empty:
    print(over_threshold.to_string(index=False))
else:
    print(f"{MIN_GAP_DAYS}日以上のカードが見つからなかったため、上位{TOP_N_ITEMS}件を表示します：")
    print(result_df.head(TOP_N_ITEMS).to_string(index=False))