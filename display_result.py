import os
import pandas as pd
import re # キーワード検索のために re をインポート

# 100点満点の「基本スコア」を計算する関数
def _calculate_base_score(row):
    """ カードの各特徴に基づき、100点満点で「基本スコア」を算出する """
    total_score = 0

    # --- 1. 還元率スコア (最大20点) ---
    try:
        cashback = float(row.get("還元率数値", 0) or 0)
        # 2.0%以上で満点とする
        cashback_score = min((cashback / 2.0) * 20, 20)
        total_score += cashback_score
    except (ValueError, TypeError):
        pass 

    # --- 2. 年会費スコア (最大20点) ---
    fee = str(row.get("年会費（税込）", ""))
    cond = str(row.get("年会費条件", ""))
    if "永年無料" in fee or ("無料" in fee and "初年度" not in fee):
        total_score += 20 
    elif "条件" in cond or "初年度無料" in fee or "条件付" in fee:
        total_score += 10 
    else: 
        try:
            fee_val_str = "".join(filter(str.isdigit, fee.replace(",", "")))
            fee_val = int(fee_val_str) if fee_val_str else 99999
            if fee_val <= 2200:
                total_score += 5 
            else:
                total_score += 1 
        except ValueError:
            total_score += 1 

    # --- 3. 保険スコア (最大15点) ---
    insurance_score = 0
    if str(row.get("旅行保険_有無", "なし")) == "あり":
        insurance_score += 5
    if (row.get("海外旅行保険数値", 0) or 0) >= 3000:
        insurance_score += 5 
    if (row.get("ショッピング保険数値", 0) or 0) > 0:
        insurance_score += 5 
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
    total_score += min(convenience_score, 15) 

    # --- 5. 国際ブランドスコア (最大10点) ---
    brands = str(row.get("国際ブランド", "")).split("/")
    brand_count = len([b for b in brands if b.strip()])
    total_score += min(brand_count * 2.5, 10) 

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

def _calculate_lifestyle_bonus(row, lifestyle_keywords, lifestyle_single):
    """ ユーザーのライフスタイル入力に基づき、ボーナス点（最大30点）を算出する """
    bonus_score = 0
    
    # --- 1. キーワードボーナス (最大15点) ---
    if lifestyle_keywords:
        # 検索対象のテキストをカードデータから結合
        search_text = " ".join([
            str(row.get("カード名", "")),
            str(row.get("メリット", "")),
            str(row.get("還元対象カテゴリ", ""))
        ]).lower() # 小文字に統一

        # 入力されたキーワードをスペースで分割（全角スペースも考慮）
        keywords = re.split(r'[\s　]+', lifestyle_keywords.lower())
        
        matched_keywords = 0
        for keyword in keywords:
            if keyword and keyword in search_text:
                matched_keywords += 1
        
        # 1キーワードヒットにつき5点、最大15点
        bonus_score += min(matched_keywords * 5, 15)

    # --- 2. 交通手段ボーナス (最大15点) ---
    if lifestyle_single:
        card_text = " ".join([
            str(row.get("カード名", "")),
            str(row.get("メリット", "")),
            str(row.get("還元対象カテゴリ", ""))
        ]).lower()

        if "電車" in lifestyle_single:
            if "suica" in card_text or "pasmo" in card_text or "交通系" in card_text or "オートチャージ" in card_text:
                bonus_score += 15
        elif "飛行機" in lifestyle_single:
            if "マイル" in card_text or "jal" in card_text or "ana" in card_text:
                bonus_score += 15
        elif "自動車" in lifestyle_single:
            if "etc" in card_text or "ガソリン" in card_text or "出光" in card_text or "eneos" in card_text:
                bonus_score += 15
                
    return bonus_score


def _fmt(x):
    s = "" if x is None else str(x).strip()
    return "" if s.lower() == "nan" else s

def _kv(label, value):
    v = _fmt(value)
    return f"<tr><th>{label}</th><td>{v}</td></tr>" if v else ""

def _generate_card_html(rank, index, r, base_score, bonus_score, total_score):
    """ 単一のカードのHTMLブロックを生成する (スコア引数を追加) """
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
    
    score_html = f"<p><strong>総合スコア：</strong>{total_score:.0f} 点</p>"
    if bonus_score > 0:
        score_html += f"""
        <p style="font-size: 0.9em; color: #007bff; margin-top: -8px;">
          (基本スコア {base_score:.0f}点 + ライフスタイルボーナス +{bonus_score:.0f}点)
        </p>
        """
    else:
        score_html += f"""
        <p style="font-size: 0.9em; color: #555; margin-top: -8px;">
          (基本スコア {base_score:.0f}点)
        </p>
        """

    return f"""
    <div class="card">
      <div class="card-header">
        <div>
          <h3>{rank}位：{_fmt(r.get('カード名'))}</h3>
          <div class="subline">{_fmt(r.get('発行会社'))} | <span class="badge {badge}">{tier}</span></div>
        </div>
        <img src="/static/images/{img}" class="card-image" alt="{_fmt(r.get('カード名'))}" loading="lazy">
      </div>
      
      {score_html} <p><strong>国際ブランド：</strong></p>
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

def display_cards(df, is_fallback=False, lifestyle_keywords="", lifestyle_single=""):
    """ Generates HTML to display a list of recommended cards sorted by score. """
    
    if df.empty:
        return "<p>エラー: カードデータ(cards.csv)の読み込みに失敗しました。</p>"

    try:
        rows_with_scores = []
        for index, row in df.iterrows():
            base_score = _calculate_base_score(row)
            bonus_score = _calculate_lifestyle_bonus(row, lifestyle_keywords, lifestyle_single)
            total_score = base_score + bonus_score
            rows_with_scores.append((index, row, base_score, bonus_score, total_score))

        # 総合スコア(total_score)でソート
        rows_with_scores.sort(key=lambda t: t[4], reverse=True) 
        
    except Exception as e:
        print(f"Error during scoring/sorting: {e}")
        return f"<p>結果の表示中にエラーが発生しました: {e}</p>"

    html = "" 

    if is_fallback:
        html += """
        <div style='background-color: #fff8e1; border: 1px solid #ffecb3; padding: 15px; border-radius: 6px; margin-bottom: 20px;'>
          <strong>該当したカードがありませんでした。</strong><br>
          おすすめのカードはこちらです。
        </div>
        """
        
        # 区分ごとに分類し、上位3件（またはそれ以下）を取得
        platinum_cards = [t for t in rows_with_scores if t[1].get("カード区分") == "プラチナ"][:3]
        gold_cards = [t for t in rows_with_scores if t[1].get("カード区分") == "ゴールド"][:3]
        general_cards = [t for t in rows_with_scores if t[1].get("カード区分") == "一般"][:3]

        if platinum_cards:
            html += "<h2 style='margin-bottom: 16px; border-bottom: 2px solid #aaa;'>おすすめのプラチナカード (Top 3)</h2>"
            for rank, (index, r, base, bonus, total) in enumerate(platinum_cards, 1):
                html += _generate_card_html(rank, index, r, base, bonus, total)
        
        if gold_cards:
            html += "<h2 style='margin-bottom: 16px; border-bottom: 2px solid #f0b400;'>おすすめのゴールドカード (Top 3)</h2>"
            for rank, (index, r, base, bonus, total) in enumerate(gold_cards, 1):
                html += _generate_card_html(rank, index, r, base, bonus, total)

        if general_cards:
            html += "<h2 style='margin-bottom: 16px; border-bottom: 2px solid #007bff;'>おすすめの一般カード (Top 3)</h2>"
            for rank, (index, r, base, bonus, total) in enumerate(general_cards, 1):
                html += _generate_card_html(rank, index, r, base, bonus, total)

    else:
       
        html += "<h2 style='margin-bottom: 16px;'>おすすめカード Top 10</h2>"
       
        for rank, (index, r, base, bonus, total) in enumerate(rows_with_scores[:10], 1): 
            html += _generate_card_html(rank, index, r, base, bonus, total)
       
    
    return html