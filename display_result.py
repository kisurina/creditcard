import os
import pandas as pd

def _score_row(row):
    """ カードの各特徴に基づき、100点満点で総合スコアを算出する """
    total_score = 0

    # --- 1. 還元率スコア (最大20点) ---
    try:
        cashback = float(row.get("還元率数値", 0) or 0)
        # 2.0%以上で満点とする
        cashback_score = min((cashback / 2.0) * 20, 20)
        total_score += cashback_score
    except (ValueError, TypeError):
        pass # エラーの場合は0点

    # --- 2. 年会費スコア (最大20点) ---
    fee = str(row.get("年会費（税込）", ""))
    cond = str(row.get("年会費条件", ""))
    if "永年無料" in fee or ("無料" in fee and "初年度" not in fee):
        total_score += 20 # 永年無料
    elif "条件" in cond or "初年度無料" in fee or "条件付" in fee:
        total_score += 10 # 条件付き無料
    else: # 有料
        try:
            fee_val_str = "".join(filter(str.isdigit, fee.replace(",", "")))
            fee_val = int(fee_val_str) if fee_val_str else 99999
            if fee_val <= 2200:
                total_score += 5 # 格安
            else:
                total_score += 1 # 一般有料
        except ValueError:
            total_score += 1 # パース失敗時は有料扱い

    # --- 3. 保険スコア (最大15点) ---
    insurance_score = 0
    if str(row.get("旅行保険_有無", "なし")) == "あり":
        insurance_score += 5
    if (row.get("海外旅行保険数値", 0) or 0) >= 3000:
        insurance_score += 5 # 海外旅行保険が3000万円以上
    if (row.get("ショッピング保険数値", 0) or 0) > 0:
        insurance_score += 5 # ショッピング保険あり
    total_score += insurance_score

    # --- 4. 利便性スコア (最大15点) ---
    convenience_score = 0
    e_money = str(row.get("電子マネー対応", ""))
    wallets = str(row.get("スマホ決済対応", ""))
    convenience_score += e_money.count("iD") * 2
    convenience_score += e_money.count("QUICPay") * 2
    convenience_score += e_money.count("交通系") * 1
    convenience_score += wallets.count("Apple Pay") * 3
    convenience_score += wallets.count("Google Pay") * 3
    total_score += min(convenience_score, 15) # 15点で頭打ち

    # --- 5. 国際ブランドスコア (最大10点) ---
    brands = str(row.get("国際ブランド", "")).split("/")
    brand_count = len([b for b in brands if b.strip()])
    total_score += min(brand_count * 2.5, 10) # 1ブランド2.5点、最大10点

    # --- 6. 空港ラウンジスコア (最大10点) ---
    lounge = str(row.get("空港ラウンジ", "なし"))
    if "国内+海外" in lounge:
        total_score += 10
    elif "国内主要空港" in lounge:
        total_score += 5
    
    # --- 7. ステータススコア (最大5点) ---
    if str(row.get("コンシェルジュ", "なし")) == "あり":
        total_score += 5

    # --- 8. 先進性スコア (最大5点) ---
    advanced_score = 0
    if str(row.get("即時発行", "なし")) == "あり":
        advanced_score += 2
    if str(row.get("番号レスカード", "なし")) == "あり":
        advanced_score += 3
    total_score += advanced_score

    return max(0, min(total_score, 100))


def _fmt(x):
    s = "" if x is None else str(x).strip()
    return "" if s.lower() == "nan" else s

def _kv(label, value):
    v = _fmt(value)
    return f"<tr><th>{label}</th><td>{v}</td></tr>" if v else ""

def _generate_card_html(rank, index, r, score):
    """ 単一のカードのHTMLブロックを生成する """
    brands = [b.strip() for b in str(r.get("国際ブランド","")).split("/") if b.strip()]
    brand_ul = "<ul class='brand-list'>" + "".join(f"<li>{b}</li>" for b in brands) + "</ul>" if brands else ""

    img = _fmt(r.get("画像ファイル名","")) or "default.png"
    img_path = os.path.join("static", "images", img)
    if not os.path.isfile(img_path):
        img = "default.png" 

    tier = _fmt(r.get("カード区分","")) or "（区分未設定）"
    badge = "badge-normal"
    if tier == "ゴールド": badge = "badge-gold"
    elif tier == "プラチナ": badge = "badge-platinum"

    return f"""
    <div class="card">
      <div class="card-header">
        <div>
          <h3>{rank}位：{_fmt(r.get('カード名'))}</h3>
          <div class="subline">{_fmt(r.get('発行会社'))} | <span class="badge {badge}">{tier}</span></div>
        </div>
        <img src="/static/images/{img}" class="card-image" alt="{_fmt(r.get('カード名'))}" loading="lazy">
      </div>
      
      <p><strong>総合スコア：</strong>{score:.0f} / 100</p>
      
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
          {_kv("入会特典有効期限", r.get("公式キャンペーン"))}
          {_kv("公式キャンペーン", r.get("公式キャンペーン"))}
          {_kv("メリット", r.get("メリット"))}
          {_kv("デメリット", r.get("デメリット"))}
        </tbody></table>
      </details>
    </div>
    """


def display_cards(df, is_fallback=False):
    """ Generates HTML to display a list of recommended cards sorted by score. """
    
    if df.empty:
        return "<p>エラー: カードデータ(cards.csv)の読み込みに失敗しました。</p>"

    try:
        rows = [(index, row, _score_row(row)) for index, row in df.iterrows()]
        # 常にスコア順でソートしておく
        rows.sort(key=lambda t: t[2], reverse=True)
    except Exception as e:
        print(f"Error during scoring/sorting: {e}")
        return f"<p>結果の表示中にエラーが発生しました: {e}</p>"

    html = "" 

    if is_fallback:
        # 0件だった場合の「代替案メッセージ」
        html += """
        <div style='background-color: #fff8e1; border: 1px solid #ffecb3; padding: 15px; border-radius: 6px; margin-bottom: 20px;'>
          <strong>該当したカードがありませんでした。</strong><br>
          おすすめのカードはこちらです。
        </div>
        """
        
        # 区分ごとに分類し、上位3件（またはそれ以下）を取得
        platinum_cards = [t for t in rows if t[1].get("カード区分") == "プラチナ"][:3]
        
        # ★★★ ここが修正された行です (余計な T[ が削除されました) ★★★
        gold_cards = [t for t in rows if t[1].get("カード区分") == "ゴールド"][:3]
        
        general_cards = [t for t in rows if t[1].get("カード区分") == "一般"][:3]

        # --- プラチナカードの表示 ---
        if platinum_cards:
            html += "<h2 style='margin-bottom: 16px; border-bottom: 2px solid #aaa;'>おすすめのプラチナカード (Top 3)</h2>"
            for rank, (index, r, score) in enumerate(platinum_cards, 1):
                html += _generate_card_html(rank, index, r, score)
        
        # --- ゴールドカードの表示 ---
        if gold_cards:
            html += "<h2 style='margin-bottom: 16px; border-bottom: 2px solid #f0b400;'>おすすめのゴールドカード (Top 3)</h2>"
            for rank, (index, r, score) in enumerate(gold_cards, 1):
                html += _generate_card_html(rank, index, r, score)

        # --- 一般カードの表示 ---
        if general_cards:
            html += "<h2 style='margin-bottom: 16px; border-bottom: 2px solid #007bff;'>おすすめの一般カード (Top 3)</h2>"
            for rank, (index, r, score) in enumerate(general_cards, 1):
                html += _generate_card_html(rank, index, r, score)

    else:
        # 通常の検索結果
        html += "<h2 style='margin-bottom: 16px;'>おすすめカード</h2>"
        for rank, (index, r, score) in enumerate(rows, 1): # Start ranking from 1
            html += _generate_card_html(rank, index, r, score)
    
    return html