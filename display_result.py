import os
import pandas as pd

def _score_row(row):
    """ Calculates a score for a single card based on its features. """
    # Safely get and convert cashback rate
    try:
        cashback = float(row.get("還元率数値", 0) or 0)
    except (ValueError, TypeError):
        cashback = 0.0
    cashback_score = min(cashback / 0.5, 5)

    # Score travel insurance presence
    insurance = str(row.get("旅行保険_有無", "なし"))
    insurance_score = 5 if "あり" in insurance else 1

    # Score annual fee
    fee = str(row.get("年会費（税込）", ""))
    cond = str(row.get("年会費条件", ""))
    if "無料" in fee and "初年度" not in fee: # Checks for permanent free fee
        fee_score = 5
    elif "条件" in cond or "初年度無料" in fee or "条件付" in fee: # Checks for conditional/first-year free
        fee_score = 3
    else: # Otherwise, assumes paid fee
        fee_score = 1

    # Score number of international brands supported
    brands = str(row.get("国際ブランド", "")).split("/")
    brand_score = min(len([b for b in brands if b.strip()]), 5) # Count non-empty brands

    # Return the total score (max 20)
    return cashback_score + insurance_score + fee_score + brand_score

def _fmt(x):
    """ Formats input to a clean string, handling None and 'nan'. """
    s = "" if x is None else str(x).strip()
    # Return empty string if the lowercased string is 'nan'
    return "" if s.lower() == "nan" else s

def _kv(label, value):
    """ Creates a table row (<tr>) for a key-value pair if the value is not empty. """
    v = _fmt(value)
    # Only return the table row HTML if the formatted value is not empty
    return f"<tr><th>{label}</th><td>{v}</td></tr>" if v else ""

def display_cards(df):
    """ Generates HTML to display a list of recommended cards sorted by score. """
    if df.empty:
        return "<p>該当するカードが見つかりませんでした。</p>"

    # Calculate scores for each card
    # Use try-except to handle potential errors during scoring
    try:
        rows = [(index, row, _score_row(row)) for index, row in df.iterrows()]
        # Sort cards by score (descending)
        rows.sort(key=lambda t: t[2], reverse=True)
    except Exception as e:
        print(f"Error during scoring/sorting: {e}")
        return f"<p>結果の表示中にエラーが発生しました: {e}</p>"


    html = "<h2 style='margin-bottom: 16px;'>おすすめカード</h2>"
    # Iterate through sorted cards and generate HTML for each
    for rank, (index, r, score) in enumerate(rows, 1): # Start ranking from 1
        # Create an unordered list (ul) for brands
        brands = [b.strip() for b in str(r.get("国際ブランド","")).split("/") if b.strip()]
        brand_ul = "<ul class='brand-list'>" + "".join(f"<li>{b}</li>" for b in brands) + "</ul>" if brands else ""

        # Determine image file, default to 'default.png' if specified image not found
        img = _fmt(r.get("画像ファイル名","")) or "default.png"
        img_path = os.path.join("static", "images", img)
        if not os.path.isfile(img_path):
            img = "default.png" # Fallback to default image
            # Consider logging a warning: print(f"Warning: Image file not found: {img_path}")

        # Determine card tier and corresponding badge class
        tier = _fmt(r.get("カード区分","")) or "（区分未設定）"
        badge = "badge-normal"
        if tier == "ゴールド": badge = "badge-gold"
        elif tier == "プラチナ": badge = "badge-platinum"

        # Construct the HTML block for the card
        html += f"""
        <div class="card">
          <div class="card-header">
            <div>
              <h3>{rank}位：{_fmt(r.get('カード名'))}</h3>
              <div class="subline">{_fmt(r.get('発行会社'))} | <span class="badge {badge}">{tier}</span></div>
            </div>
            <img src="/static/images/{img}" class="card-image" alt="{_fmt(r.get('カード名'))}" loading="lazy">
          </div>
          <p><strong>総合スコア：</strong>{score:.1f} / 20</p>
          <p><strong>国際ブランド：</strong></p>
          {brand_ul}

          <details class="details">
            <summary>詳細を開く</summary>
            <table class="kv"><tbody>
              {_kv("年会費（税込）", r.get("年会費（税込）"))}
              {_kv("年会費条件", r.get("年会費条件"))}
              {_kv("還元率_基本（%）", r.get("還元率_基本（%）"))}
              {_kv("ボーナス還元率（%）", r.get("ボーナス還元率（%）"))}
              {_kv("還元対象カテゴリ", r.get("還元対象カテゴリ"))}
              {_kv("還元上限（月額）", r.get("還元上限（月額）"))}
              {_kv("ポイントプログラム名", r.get("ポイントプログラム名"))}
              {_kv("ポイント換算（円→P）", r.get("ポイント換算（円→P）"))}
              {_kv("旅行保険_有無", r.get("旅行保険_有無"))}
              {_kv("海外旅行保険_付帯種別", r.get("海外旅行保険_付帯種別"))}
              {_kv("海外旅行保険_最高補償額（万円）", r.get("海外旅行保険_最高補償額（万円）"))}
              {_kv("ショッピング保険_年間補償額（万円）", r.get("ショッピング保険_年間補償額（万円）"))}
              {_kv("電子マネー対応", r.get("電子マネー対応"))}
              {_kv("タッチ決済対応", r.get("タッチ決済対応"))}
              {_kv("スマホ決済対応", r.get("スマホ決済対応"))}
              {_kv("空港ラウンジ", r.get("空港ラウンジ"))}
              {_kv("コンシェルジュ", r.get("コンシェルジュ"))}
              {_kv("ETC_可否", r.get("ETC_可否"))}
              {_kv("ETC_年会費", r.get("ETC_年会費"))}
              {_kv("家族カード可否", r.get("家族カード可否"))}
              {_kv("即時発行", r.get("即時発行"))}
              {_kv("バーチャルカード対応", r.get("バーチャルカード対応"))}
              {_kv("番号レスカード", r.get("番号レスカード"))}
              {_kv("申込対象", r.get("申込対象"))}
              {_kv("入会特典ポイント", r.get("入会特典ポイント"))}
              {_kv("入会特典有効期限", r.get("入会特典有効期限"))}
              {_kv("公式キャンペーン", r.get("公式キャンペーン"))}
              {_kv("メリット", r.get("メリット"))}
              {_kv("デメリット", r.get("デメリット"))}
            </tbody></table>
          </details>
        </div>
        """
    return html

