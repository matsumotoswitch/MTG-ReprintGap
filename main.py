import json
import pandas as pd

# --- 設定（定数） ---
DATA_FILE = "default-cards-20260516091059.json"
MIN_GAP_DAYS = 10000
TOP_N_ITEMS = 30
# --------------------

# 1. Scryfallのバルクデータを読み込み
print("データを読み込み中...")
with open(DATA_FILE, "r", encoding="utf-8") as f:
    cards = json.load(f)

card_prints = []

print("データを抽出中...")
for card in cards:
    # デジタル専用セット（MTGO/アリーナ限定）を除外
    if card.get("digital"):
        continue

    # 基本土地を除外（Forest, Island, Mountain, Swamp, Plains, Wastes）
    # ※これを入れないと基本土地のデータがノイズになります
    if "Basic Land" in card.get("type_line", ""):
        continue
        
    # トークン、両面トークン、紋章、カード裏面、アートカード、およびトークンセットなどを完全に除外
    if card.get("layout") in ["token", "double_faced_token", "emblem", "art_series"] or card.get("set_type") == "token" or "Token" in card.get("type_line", ""):
        continue
        
    # 公式大会で使用できないカード（印刷）を包括的に除外
    # - 銀枠（ジョークセット）、金枠
    if card.get("border_color") in ["silver", "gold"]:
        continue
    # - 記念品（30A、コレクターズエディションなど）
    if card.get("set_type") == "memorabilia":
        continue
    # - どんぐりスタンプ（Unfinityの非公式カード）
    if card.get("security_stamp") == "acorn":
        continue
    # - 大判カード、厚紙、プレイテストカードなど
    if card.get("oversized") or "playtest" in card.get("promo_types", []) or "thick" in card.get("promo_types", []):
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

# 2. 空白期間の計算
max_gaps = []

print("空白期間を計算中...")
for oracle_id, group in df.groupby("oracle_id"):
    if len(group) < 2:
        continue # 再録が一度もないカードはスキップ
    
    # 発売日順にソートし、安全に行を取得できるようインデックスをリセット
    group = group.sort_values("released_at").reset_index(drop=True)
    card_name = group["name"].iloc[0]
    
    # 隣り合う印刷（セット）の発売日差（日数）を計算
    group["prev_released_at"] = group["released_at"].shift(1)
    group["prev_set"] = group["set"].shift(1)
    group["gap_days"] = (group["released_at"] - group["prev_released_at"]).dt.days
    
    # そのカードにおける最大の空白期間を持つ行（インデックス）を取得
    max_gap_idx = group["gap_days"].idxmax()
    max_gap_row = group.loc[max_gap_idx]
    
    max_gaps.append({
        "name": card_name,
        "prev_set": max_gap_row["prev_set"].upper(),
        "next_set": max_gap_row["set"].upper(),
        "prev_date": max_gap_row["prev_released_at"].strftime('%Y-%m-%d'),
        "next_date": max_gap_row["released_at"].strftime('%Y-%m-%d'),
        "gap_days": int(max_gap_row["gap_days"])
    })

# 結果をソート
result_df = pd.DataFrame(max_gaps)
result_df = result_df.sort_values(by="gap_days", ascending=False)

# 3. 指定された日数以上のカード、または上位N件を表示
print("\n=== 再録までの空白期間が長かったカード ===")
over_threshold = result_df[result_df["gap_days"] >= MIN_GAP_DAYS]

if not over_threshold.empty:
    print(over_threshold.to_string(index=False))
else:
    print(f"{MIN_GAP_DAYS}日以上のカードが見つからなかったため、上位{TOP_N_ITEMS}件を表示します：")
    print(result_df.head(TOP_N_ITEMS).to_string(index=False))