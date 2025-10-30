from flask import Flask, render_template, request
from filter_logic import filter_cards
from display_result import display_cards
import json

app = Flask(__name__)


# CHECKBOX_GROUPS defines the filter options displayed on the webpage.
CHECKBOX_GROUPS = {
    "tiers": {"title": "カード区分", "items": ["一般", "ゴールド", "プラチナ"]},
    "brands": {"title": "国際ブランド（いずれか含む）", "items": ["VISA", "MasterCard", "JCB", "American Express", "Diners"]},
    "points": {"title": "貯まるポイントで選ぶ（いずれか含む）", "items": ["Vポイント", "楽天ポイント", "Pontaポイント", "dポイント", "マイル"]},
    "applicant_type": {"title": "申込対象で選ぶ（いずれか含む）", "items": ["学生可", "20歳以上", "高校生を除く18歳以上"]},
    "insurance": {"title": "保険で選ぶ（すべて満たす）", "items": ["海外旅行保険あり", "国内旅行保険あり", "ショッピング保険あり"]},
    "e_money": {"title": "電子マネー（すべて対応）", "items": ["iD", "QUICPay", "交通系", "WAON", "楽天Edy"]},
    "wallets": {"title": "スマホウォレット（すべて対応）", "items": ["Apple Pay", "Google Pay", "おサイフケータイ"]},
    "features": {"title": "欲しい機能（すべて満たす）", "items": ["年会費無料", "空港ラウンジ", "コンシェルジュ", "タッチ決済", "ETC無料", "家族カード", "即時発行", "バーチャルカード", "番号レス"]},
    "campaigns": {"title": "キャンペーン条件", "items": ["入会特典あり"]}
}

@app.route("/")
def index():
    """ Renders the main page with the diagnosis form. """
    return render_template("index.html", show_form=True, groups=CHECKBOX_GROUPS)

@app.route("/diagnose", methods=["POST"])
def diagnose():
    """ Handles the form submission and displays card results. """
    # Handle optional amount input. If empty, set to -1 as a flag.
    amount_str = request.form.get("amount")
    if amount_str and amount_str.isdigit():
        amount = int(amount_str)
    else:
        amount = -1

    # Get other form values
    rate = float(request.form.get("cashback", 0))
    keyword = request.form.get("keyword", "").strip()

    # Get all checkbox list values
    tiers = request.form.getlist("tiers")
    brands = request.form.getlist("brands")
    e_money = request.form.getlist("e_money")
    wallets = request.form.getlist("wallets")
    features = request.form.getlist("features")
    campaigns = request.form.getlist("campaigns")
    points = request.form.getlist("points")
    applicant_type = request.form.getlist("applicant_type")
    insurance = request.form.getlist("insurance")

    campaign_has_bonus = "入会特典あり" in campaigns

    # Call the filtering function with all user criteria
    filtered = filter_cards(
        amount=amount,
        min_rate=rate,
        tiers=tiers,
        brands=brands,
        features=features,
        e_money=e_money,
        wallets=wallets,
        campaign_has_bonus=campaign_has_bonus,
        keyword=keyword,
        points=points,
        applicant_type=applicant_type,
        insurance=insurance
    )
    
    # Generate HTML for the results
    results_html = display_cards(filtered)

    # Render the page with the results
    return render_template(
        "index.html",
        show_form=False,
        results_html=results_html,
        groups=CHECKBOX_GROUPS
    )

if __name__ == "__main__":
    app.run(debug=True)

