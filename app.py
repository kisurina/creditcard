from flask import Flask, render_template, request
from filter_logic import filter_cards
from display_result import display_cards
import json

app = Flask(__name__)


# CHECKBOX_GROUPS defines the filter options displayed on the webpage.
CHECKBOX_GROUPS = {
    # ★★★ 「よく利用するお店(複数可)」が削除されました ★★★

    "lifestyle_single": {
        "title": "【ライフスタイル診断】主な交通手段は？ (いずれか一つ)",
        "items": [
            "電車 (Suica / PASMOなど)",
            "飛行機 (マイルを貯めたい)",
            "自動車 (ETC / ガソリン)"
        ]
    },

    "tiers": {"title": "【カードスペック】カード区分", "items": ["一般", "ゴールド", "プラチナ"]},
    "brands": {
        "title": "【カードスペック】国際ブランド（いずれか含む）", 
        "items": [
            {"name": "VISA", "desc": "世界シェアNo.1の決済網。国内外問わず、実店舗でもオンラインでも「使えない場所がほぼない」圧倒的な安心感が強みです。"},
            {"name": "MasterCard", "desc": "VISAに次ぐ世界No.2のシェア。特にヨーロッパ圏での決済に強く、日本ではコストコで使える国際ブランドとしても知られています。"},
            {"name": "JCB", "desc": "日本発祥の唯一の国際ブランド。国内加盟店が非常に多く、ハワイやグアム、韓国など日本人観光客が多いエリアでの優待が手厚いのが特徴です。"},
            {"name": "American Express", "desc": "高いステータスと信頼性が特徴。空港ラウンジ、手厚い旅行保険、コンシェルジュサービスなど、旅行やエンタメ関連の特典が群を抜いて充実しています。"},
            {"name": "Diners", "desc": "Amexと並ぶ、あるいはそれ以上のステータスを持つ最上位ブランド。特に高級レストランでのコース料理1名分無料サービスなど、グルメ系の優待に圧倒的な強みを持っています。"}
        ]
    },
    "points": {"title": "【カードスペック】貯まるポイントで選ぶ（いずれか含む）", "items": ["Vポイント", "楽天ポイント", "Pontaポイント", "dポイント", "マイル"]},
    "applicant_type": {"title": "【カードスペック】申込対象で選ぶ（いずれか含む）", "items": ["学生可", "20歳以上", "高校生を除く18歳以上"]},
    "insurance": {"title": "【カードスペック】保険で選ぶ（すべて満たす）", "items": ["海外旅行保険あり", "国内旅行保険あり", "ショッピング保険あり"]},
    "e_money": {"title": "【カードスペック】電子マネー（すべて対応）", "items": ["iD", "QUICPay", "交通系", "WAON", "楽天Edy"]},
    "wallets": {"title": "【カードスペック】スマホウォレット（すべて対応）", "items": ["Apple Pay", "Google Pay", "おサイフケータイ"]},
    "features": {"title": "【カードスペック】欲しい機能（すべて満たす）", "items": ["年会費無料", "空港ラウンジ", "コンシェルジュ", "タッチ決済", "ETC無料", "家族カード", "即時発行", "バーチャルカード", "番号レス"]},
    "campaigns": {"title": "【カードスペック】キャンペーン条件", "items": ["入会特典あり"]}
}

@app.route("/")
def index():
    """ Renders the main page with the diagnosis form. """
    return render_template("index.html", show_form=True, groups=CHECKBOX_GROUPS)

@app.route("/diagnose", methods=["POST"])
def diagnose():
    """ Handles the form submission and displays card results. """
    amount_str = request.form.get("amount")
    if amount_str and amount_str.isdigit():
        amount = int(amount_str)
    else:
        amount = -1

    keyword = request.form.get("keyword", "").strip()

    tiers = request.form.getlist("tiers")
    brands = request.form.getlist("brands")
    e_money = request.form.getlist("e_money")
    wallets = request.form.getlist("wallets")
    features = request.form.getlist("features")
    campaigns = request.form.getlist("campaigns")
    points = request.form.getlist("points")
    applicant_type = request.form.getlist("applicant_type")
    insurance = request.form.getlist("insurance")

    # ★★★ ここがキーワード入力に変更されました ★★★
    lifestyle_keywords = request.form.get("lifestyle_keywords", "").strip()
    lifestyle_single = request.form.get("lifestyle_single", "") 

    campaign_has_bonus = "入会特典あり" in campaigns

    # フィルター関数を呼び出し
    filtered_df, is_fallback = filter_cards(
        amount=amount,
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
    
    # ★★★ display_cards にキーワードを渡すよう変更 ★★★
    results_html = display_cards(
        filtered_df, 
        is_fallback,
        lifestyle_keywords=lifestyle_keywords,
        lifestyle_single=lifestyle_single
    )

    # Render the page with the results
    return render_template(
        "index.html",
        show_form=False,
        results_html=results_html,
        groups=CHECKBOX_GROUPS
    )

if __name__ == "__main__":
    app.run(debug=True)