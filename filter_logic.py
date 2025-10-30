import pandas as pd
import re

def load_cards(file_path="cards.csv"):
    """ Loads and preprocesses the card data from a CSV file. """
    try:
        # Skip lines with parsing errors to prevent crashes
        df = pd.read_csv(file_path, on_bad_lines='skip')
    except pd.errors.ParserError as e:
        print(f"CSV parsing error: {e}")
        return pd.DataFrame()
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return pd.DataFrame()


    # Create numeric columns for easier filtering and scoring
    numeric_cols = {
        "還元率_基本（%）": "還元率数値",
        "海外旅行保険_最高補償額（万円）": "海外旅行保険数値",
        "ショッピング保険_年間補償額（万円）": "ショッピング保険数値"
    }
    for original_col, new_col in numeric_cols.items():
        if original_col in df.columns:
            df[new_col] = pd.to_numeric(df[original_col], errors='coerce').fillna(0)
        else:
            df[new_col] = 0.0 # Assign default value if column doesn't exist

    # Ensure all required text columns exist to prevent errors during filtering
    required_cols = [
        "カード名","発行会社","カード区分","国際ブランド","年会費（税込）","年会費条件",
        "旅行保険_有無","画像ファイル名","月々の推奨利用額","電子マネー対応",
        "タッチ決済対応","スマホ決済対応","空港ラウンジ","コンシェルジュ",
        "ETC_年会費","ETC_可否","家族カード可否","即時発行","バーチャルカード対応","番号レスカード",
        "メリット","デメリット","入会特典ポイント","入会特典有効期限","公式キャンペーン", "申込対象", "ポイントプログラム名"
    ]
    for col in required_cols:
        if col not in df.columns:
            df[col] = "" # Add missing columns with empty strings

    return df

def _has_bonus(text):
    """ Checks if a card has a sign-up bonus based on the text. """
    s = str(text).strip()
    if not s or s.lower() == "nan":
        return False
    # Check for any digit
    if re.search(r'\d', s):
        nums = re.findall(r'[0-9,]+', s)
        try:
            # Check if the first number found is greater than 0
            if nums:
                val = int(nums[0].replace(',', ''))
                return val > 0
            else: # Contains digits but not in expected number format, assume bonus
                return True
        except (ValueError, IndexError):
            return True # Error during conversion, but text exists
    elif len(s) > 0: # Non-empty string without digits
         return True
    else: # Empty string
         return False


def filter_cards(amount=-1, min_rate=0.0, tiers=None, brands=None, features=None, e_money=None, wallets=None, campaign_has_bonus=False, keyword="", points=None, applicant_type=None, insurance=None):
    """ Filters the DataFrame of cards based on various user-selected criteria. """
    df = load_cards()
    if df.empty:
        return df

    filtered = df.copy()

    # --- Apply Filters Sequentially ---

    # Filter by monthly usage amount (skipped if amount is -1)
    if amount != -1:
        if amount <= 10000: usage = "～1万円"
        elif amount <= 30000: usage = "1万円～3万円"
        elif amount <= 50000: usage = "3万円～5万円"
        else: usage = "5万円～"
        # Filter only if the column exists and has relevant data
        if "月々の推奨利用額" in filtered.columns and filtered["月々の推奨利用額"].notna().any():
            # Ensure comparison is done on stripped strings
            filtered = filtered[filtered["月々の推奨利用額"].astype(str).str.strip() == usage]

    # Filter by cashback rate
    if "還元率数値" in filtered.columns:
        filtered = filtered[filtered["還元率数値"] >= float(min_rate)]

    # Filter by card tiers
    if tiers:
        filtered = filtered[filtered["カード区分"].isin(tiers)]

    # Filter by brands (OR logic)
    if brands:
        # Fill NaN with empty string before applying string methods
        filtered = filtered[filtered["国際ブランド"].fillna("").astype(str).apply(lambda s: any(b in s for b in brands))]

    # Filter by e-money (AND logic)
    if e_money:
        filtered = filtered[filtered["電子マネー対応"].fillna("").astype(str).apply(lambda s: all(em in s for em in e_money))]

    # Filter by wallets (AND logic)
    if wallets:
        filtered = filtered[filtered["スマホ決済対応"].fillna("").astype(str).apply(lambda s: all(w in s for w in wallets))]

    # Filter by point type (OR logic)
    if points:
        point_masks = []
        for p in points:
            keyword_to_search = "マイル" if "マイル" in p else p.replace("ポイント", "")
            # Check in both 'ポイントプログラム名' and 'メリット' columns
            mask = (
                filtered["ポイントプログラム名"].fillna("").str.contains(keyword_to_search, case=False, regex=False) |
                filtered["メリット"].fillna("").str.contains(keyword_to_search, case=False, regex=False)
            )
            point_masks.append(mask)
        # Combine masks with OR logic if multiple points are selected
        if point_masks:
            combined_mask = pd.concat(point_masks, axis=1).any(axis=1)
            filtered = filtered[combined_mask]

    # Filter by applicant type (OR logic)
    if applicant_type:
        filtered = filtered[filtered["申込対象"].fillna("").astype(str).apply(lambda s: any(at in s for at in applicant_type))]

    # Filter by insurance types (AND logic)
    if insurance:
        for ins in insurance:
            if ins == "海外旅行保険あり":
                filtered = filtered[filtered["海外旅行保険数値"] > 0]
            elif ins == "国内旅行保険あり":
                # Check if travel insurance exists AND mentions "国内" (domestic)
                mask1 = filtered["旅行保険_有無"].fillna("").str.contains("あり")
                mask2 = filtered["メリット"].fillna("").str.contains("国内") | filtered["デメリット"].fillna("").str.contains("国内")
                # More robust check if a specific domestic insurance column exists could be added
                filtered = filtered[mask1 & mask2] # Apply both conditions
            elif ins == "ショッピング保険あり":
                filtered = filtered[filtered["ショッピング保険数値"] > 0]

    # Keyword Search (searches only card name and issuer)
    if keyword:
        search_cols = ["カード名", "発行会社"]
        # Create mask based on keyword presence in specified columns (case-insensitive)
        mask = filtered[search_cols].fillna("").astype(str).apply(
            lambda x: x.str.lower().str.contains(keyword.lower(), na=False, regex=False)
        ).any(axis=1)
        filtered = filtered[mask]

    # Filter by other features (AND logic, using vectorized operations)
    feat_list = features or []
    if feat_list:
        for f in feat_list:
            # Check column existence before applying filter
            if f == "年会費無料" and "年会費（税込）" in filtered.columns:
                filtered = filtered[filtered["年会費（税込）"].fillna("").str.contains("無料")]
            elif f == "空港ラウンジ" and "空港ラウンジ" in filtered.columns:
                # Exclude empty strings and 'なし'
                filtered = filtered[filtered["空港ラウンジ"].fillna("").str.strip().ne("") & filtered["空港ラウンジ"].fillna("").str.strip().ne("なし")]
            elif f == "コンシェルジュ" and "コンシェルジュ" in filtered.columns:
                filtered = filtered[filtered["コンシェルジュ"].fillna("").str.contains("あり")]
            elif f == "タッチ決済" and "タッチ決済対応" in filtered.columns:
                # Exclude empty, 'nan', and 'なし'
                filtered = filtered[filtered["タッチ決済対応"].fillna("").str.strip().ne("") & filtered["タッチ決済対応"].fillna("").str.lower().ne("nan") & filtered["タッチ決済対応"].fillna("").str.strip().ne("なし")]
            elif f == "ETC無料" and "ETC_年会費" in filtered.columns:
                filtered = filtered[filtered["ETC_年会費"].fillna("").str.contains("無料")]
            elif f == "家族カード" and "家族カード可否" in filtered.columns:
                filtered = filtered[filtered["家族カード可否"].fillna("").str.contains("あり")]
            elif f == "即時発行" and "即時発行" in filtered.columns:
                filtered = filtered[filtered["即時発行"].fillna("").str.contains("あり")]
            elif f == "バーチャルカード" and "バーチャルカード対応" in filtered.columns:
                filtered = filtered[filtered["バーチャルカード対応"].fillna("").str.contains("あり")]
            elif f == "番号レス" and "番号レスカード" in filtered.columns:
                filtered = filtered[filtered["番号レスカード"].fillna("").str.contains("あり")]

    # Filter by campaign bonus presence
    if campaign_has_bonus and "入会特典ポイント" in filtered.columns:
        filtered = filtered[filtered["入会特典ポイント"].apply(_has_bonus)]

    return filtered

