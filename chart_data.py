import pandas as pd 

def _score_row(row):
    
    cashback_text = row.get("還元率数値", 0)
    try:
        cashback = float(cashback_text) if cashback_text is not None else 0.0
    except (ValueError, TypeError):
        cashback = 0.0
    cashback_score = min(cashback / 0.5, 5)

    insurance = str(row.get("旅行保険_有無", "なし"))
    insurance_score = 5 if "あり" in insurance else 1

    fee = str(row.get("年会費（税込）", ""))
    cond = str(row.get("年会費条件", ""))
    if "無料" in fee and "初年度" not in fee:
        fee_score = 5
    elif "条件" in cond or "初年度無料" in fee or "条件付" in fee:
        fee_score = 3
    else:
        fee_score = 1

    brands = str(row.get("国際ブランド", "")).split("/")
    brand_score = min(len([b for b in brands if b.strip()]), 5)

    return cashback_score + insurance_score + fee_score + brand_score

def prepare_chart_data(df):
    chart_list = []
    if not df.empty:
        try:
            for _, row in df.iterrows():

                label = row.get("カード名", "不明なカード")
                score = _score_row(row)
                chart_list.append({"label": label, "score": score})

            chart_list.sort(key=lambda item: item['score'], reverse=True)
        except Exception as e:
            print(f"チャートデータ準備中にエラー: {e}")

            return []