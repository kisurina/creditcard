import re
import pandas as pd # Added import for type hinting

def _parse_yen_to_int(fee_str: str) -> int:
    """ Parses annual fee string (e.g., "11,000円", "3.3万", "無料") to an integer amount in yen. Returns 0 if free or parsing fails. """
    if not fee_str:
        return 0
    s = str(fee_str).strip() # Convert to string and remove whitespace
    if "無料" in s or "0円" in s:
        return 0

    # Pattern for "xxxx円"
    m = re.search(r'([\d,]+)\s*円', s)
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            pass # Continue to next pattern if conversion fails

    # Pattern for "x.x万"
    m2 = re.search(r'([\d\.]+)\s*万', s)
    if m2:
        try:
            return int(float(m2.group(1)) * 10000)
        except ValueError:
            pass # Continue to next pattern

    # Pattern for digits only (potentially with commas)
    m3 = re.search(r'^([\d,]+)$', s) # Match the whole string
    if m3:
        try:
            return int(m3.group(1).replace(",", ""))
        except ValueError:
            pass

    # Fallback: find first sequence of digits if other patterns fail
    nums = re.findall(r'([\d,]+)', s)
    if nums:
        try:
            return int(nums[0].replace(",", ""))
        except ValueError:
            pass

    # print(f"Warning: Failed to parse annual fee: '{fee_str}'") # Optional warning
    return 0 # Return 0 if parsing fails

def infer_card_tier(row: pd.Series) -> str:
    """
    Infers card tier ('プラチナ' / 'ゴールド' / '一般') based on card name keywords and annual fee.
    Priority: Name Keyword > Annual Fee Threshold.
    Args:
        row (pd.Series): A row from the card DataFrame.
    Returns:
        str: The inferred card tier.
    """
    # Get card name and fee, default to empty string if missing
    name = str(row.get("カード名", "")).strip()
    fee_text = str(row.get("年会費（税込）", "")).strip()

    # Check name keywords first
    if "プラチナ" in name:
        return "プラチナ"
    if "ゴールド" in name:
        # Add exceptions here if needed (e.g., "ヤングゴールド" is not Gold)
        return "ゴールド"

    # If no keyword matches, check annual fee
    fee_yen = _parse_yen_to_int(fee_text)

    if fee_yen >= 30000:
        return "プラチナ"
    if fee_yen >= 10000:
        return "ゴールド"

    # Default to '一般'
    return "一般"

def add_card_tier(df: pd.DataFrame) -> pd.DataFrame:
    """ Adds 'カード区分' (tier) and 'カードランクスコア' (tier score) columns to the DataFrame.
        If 'カード区分' already exists and has values, it calculates the score based on existing tiers.
        Otherwise, it infers the tier using infer_card_tier.
    Args:
        df (pd.DataFrame): The input DataFrame.
    Returns:
        pd.DataFrame: DataFrame with added tier and score columns.
    """
    df_copy = df.copy() # Work on a copy to avoid modifying the original DataFrame

    # Check if 'カード区分' needs inference or already exists
    if "カード区分" not in df_copy.columns or df_copy["カード区分"].isnull().all() or (df_copy["カード区分"] == "").all():
        print("Inferring 'カード区分' based on name and fee.")
        # Apply inference function row by row
        df_copy["カード区分"] = df_copy.apply(infer_card_tier, axis=1)
    else:
        print("Using existing 'カード区分' column.")

    # Map tier name to a numerical score
    tier_score_map = {"一般": 1, "ゴールド": 2, "プラチナ": 3}
    # Apply map, fill missing/unknown tiers with score 1 (General)
    df_copy["カードランクスコア"] = df_copy["カード区分"].map(tier_score_map).fillna(1).astype(int)

    return df_copy

