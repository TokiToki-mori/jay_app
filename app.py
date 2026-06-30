import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json
import time
import base64

# 1. ページの設定
st.set_page_config(page_title="JAY コミュニティアプリ", page_icon="🪙", layout="centered")

# 🔗 【★本当の最新URL】今モリケンタロウさんが発行してくださった本物のGAS URLです
GAS_URL = "https://script.google.com/macros/s/AKfycbyy4RIstldrA7Zruat1zdGTIwqvjcvyWHGtgvDffT2DNYrNfUj2SqOhN_NPfd8wEAI/exec"

# 📊 Googleスプレッドシートからすべてのデータを一括で取得する関数
def get_all_data():
    try:
        response = requests.get(GAS_URL)
        if response.status_code == 200:
            return response.json()
        return {"members": [], "history": [], "products": [], "comments": []}
    except Exception:
        return {"members": [], "history": [], "products": [], "comments": []}

# 🔄 最初に一括で全データを読み込む
all_data = get_all_data()

# ==========================================
# 👤 【★データ不整合の完全撲滅ロジック】
# ==========================================
raw_members = all_data.get("members", [])
MEMBER_LIST = ["選択してください"]
PASSWORD_DICT = {}
BALANCE_DICT = {} 

# 他のシート（過去ログなど）からは一切拾わず、GASの「会員名簿」の配列だけを厳密に処理
for m in raw_members:
    if isinstance(m, list) and len(m) >= 1:
        name = str(m[0]).strip()
        
        # 名前が空っぽでなければ、ドロップダウンの絶対的な正解リストに追加
        if name and name != "" and name != "undefined":
            MEMBER_LIST.append(name)
            
            # 2番目の要素（パスワード）を安全に取得
            if len(m) >= 2 and m[1] is not None and str(m[1]).strip() != "":
                PASSWORD_DICT[name] = str(m[1]).strip().split('.')[0].zfill(4)
            else:
                PASSWORD_DICT[name] = ""
                
            # 3番目の要素（スプレッドシートのD列の計算残高）を100%そのまま無加工で取得
            if len(m) >= 3 and m[2] is not None:
                try:
                    BALANCE_DICT[name] = int(float(str(m[2]).strip()))
                except ValueError:
                    BALANCE_DICT[name] = 3000
            else:
                BALANCE_DICT[name] = 3000

all_history = all_data.get("history", [])
all_products = all_data.get("products", [])
all_comments = all_data.get("comments", [])

# --- 画面全体のタイトル ---
st.title("✨ コミュニティ通貨 JAY 総合システム")
st.write("感謝の送金と、メンバー同士の商品・サービスバザールを循環させましょう。")

st.markdown("---")

# ==========================================
# 👤 暗証番号認証付きログイン配置
# ==========================================
st.subheader("👤 あなたのお名前を選択してください")
sender = st.selectbox("お名前を選ぶと、残高確認や投稿・コメントができるようになります", MEMBER_LIST, key="global_user", label_visibility="collapsed")

# 認証フラグの初期化
authenticated = False

if sender != "選択してください":
    correct_password = PASSWORD_DICT.get(sender, "")
    
    if correct_password:
        input_password = st.text_input("🔑 4桁の暗証番号（誕生日など）を入力してください", type="password", max_chars=4)
        
        if input_password:
            if input_password.strip().zfill(4) == correct_password:
                authenticated = True
                current_balance = BALANCE_DICT.get(sender, 3000)
                st.success(f"🔓 認証成功！ {sender} さんとしてログインしました。")
                st.info(f"💰 **現在の所持残高: {current_balance} JAY**")
            else:
                st.error("❌ 暗証番号が一致しません。もう一度ご確認ください。")
    else:
        # パスワードが未登録の場合はそのまま通す
        authenticated = True
        current_balance = BALANCE_DICT.get(sender, 3000)
        st.info(f"💰 **{sender} さんの現在の所持残高: {current_balance} JAY** (※暗証番号が未登録です)")
else:
    st.warning("⚠️ 最初にお名前を選択してください。選択するまで以下の機能は利用できません。")

st.markdown("---")

# 認証が成功している場合のみ、送金・掲示板を表示
if authenticated:
    current_balance = BALANCE_DICT.get(sender, 3000)
    
    tab1, tab2 = st.tabs(["🏪 JAY商品バザール掲示板", "💝 感謝のJAY送金"])

    # ==========================================
    # 🏪 タブ1：JAY商品バザール掲示板画面
    # ==========================================
    with tab1:
        bazaar_mode = st.radio("メニューを選んでください", ["📦 出品されている商品を見る", "➕ 新しい商品・サービスを出品する"], horizontal=True)
        
        if bazaar_mode == "➕ 新しい商品・サービスを出品する":
            st.subheader("📝 新しい商品・サービスを出品する")
            
            prod_title = st.text_input("タイトル（商品名・サービス名）", placeholder="例：無農薬の新タマネギ譲ります！")
            prod_category = st.selectbox("カテゴリ", ["物品（譲る・売る）", "スキル・お手伝い", "その他"])
            prod_desc = st.text_area("詳しい内容・提供可能日時など", placeholder="商品の詳細や、サービスを提供できる日時などを詳しく書いてください。")
            prod_price = st.number_input("必要なJAY", min_value=0, value=100, step=50)
            prod_delivery = st.selectbox("受け渡し方法", ["手渡し", "郵送", "オンライン"])
            prod_delivery_detail = st.text_area("受け渡しの詳細", placeholder="例：山口市内の〇〇駅周辺で手渡し希望です。など")
            
            uploaded_file = st.file_uploader("写真をアップロード（JPEG/PNG）", type=["jpg", "jpeg", "png"])
            
            if st.button("🚀 この内容で掲示板に出品する", use_container_width=True):
                if not prod_title:
                    st.error("❌ 商品のタイトルを入力してください。")
                else:
                    final_image_string = "https://images.unsplash.com/photo-1511556532299-8f662fc26c06?w=300"
                    
                    if uploaded_file is not None:
                        try:
                            file_bytes = uploaded_file.getvalue()
                            encoded_string = base64.b64encode(file_bytes).decode("utf-8")
                            mime_type = uploaded_file.type
                            final_image_string = f"data:{mime_type};base64,{encoded_string}"
                        except Exception as e:
                            st.error(f"❌ 画像の処理中にエラーが発生しました: {str(e)}")
                    
                    data = {
                        "action": "add_product",
                        "sender": sender,
                        "title": prod_title,
                        "category": prod_category,
                        "description": prod_desc,
                        "amount": prod_price,
                        "delivery_method": prod_delivery,
                        "delivery_detail": prod_delivery_detail,
                        "image_data": "uploaded",
                        "image_name": "image.jpg",
                        "image_url": final_image_string
                    }
                    
                    with st.spinner("🔄 スプレッドシートに商品情報を記録中..."):
                        res = requests.post(GAS_URL, data=json.dumps(data))
                        if res.status_code == 200:
                            st.success("🎉 掲示板への出品が完了しました！")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
        else:
            st.subheader("💬 出品中のアイテム一覧")
            
            if not all_products:
                st.info("現在、出品されている商品はありません。最初の出品をしてみましょう！")
            else:
                for prod in reversed(all_products):
                    with st.expander(f"【{prod['status']}】 {prod['title']} — 🪙 {prod['amount']} JAY （出品：{prod['sender']}さん）", expanded=True):
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            img_url = prod.get('image_url', '')
                            default_img = "https://images.unsplash.com/photo-1511556532299-8f662fc26c06?w=300"
                            if isinstance(img_url, str) and (img_url.startswith("http") or img_url.startswith("data:image")):
                                try:
                                    st.image(img_url, use_container_width=True)
                                except Exception:
                                    st.image(default_img, use_container_width=True)
                            else:
                                st.image(default_img, use_container_width=True)
                                
                        with col2:
                            st.markdown(f"**🏷️ カテゴリ:** {prod['category']}")
                            st.markdown(f"**🤝 受け渡し:** {prod['delivery_method']}")
                            st.markdown(f"**📍 受け渡し詳細:** {prod['delivery_detail']}")
                            st.info(f"📝 **詳しい内容:**\n{prod['description']}")
                        
                        if sender == prod['sender']:
                            st.markdown("⚙️ **出品者専用管理パネル**")
                            edit_col1, edit_col2, edit_col3 = st.columns([2, 2, 1])
                            
                            with edit_col1:
                                new_price = st.number_input("JAY数を変更", min_value=0, value=int(prod['amount']), step=50, key=f"price_{prod['id']}")
                            with edit_col2:
                                new_status = st.selectbox("ステータス変更", ["🟢 受付中", "🔴 取引完了（受付終了）"], index=0 if prod['status'] == "🟢 受付中" else 1, key=f"status_{prod['id']}")
                            with edit_col3:
                                st.write("")
                                st.write("")
                                delete_btn = st.button("🗑️ 削除", key=f"del_{prod['id']}", type="primary")
                            
                            if st.button("📝 上記の変更（JAY数・ステータス）を反映する", key=f"save_{prod['id']}", use_container_width=True):
                                u_data = {
                                    "action": "update_product",
                                    "product_id": prod["id"],
                                    "amount": new_price,
                                    "status": new_status
                                }
                                with st.spinner("🔄 商品情報を更新中..."):
                                    res = requests.post(GAS_URL, data=json.dumps(u_data))
                                    if res.status_code == 200:
                                        st.success("✅ 商品情報を更新しました！")
                                        time.sleep(1)
                                        st.rerun()
                                        
                            if delete_btn:
                                d_data = {
                                    "action": "delete_product",
                                    "product_id": prod["id"]
                                }
                                with st.spinner("🗑️ 商品を削除中..."):
                                    res = requests.post(GAS_URL, data=json.dumps(d_data))
                                    if res.status_code == 200:
                                        st.success("💥 商品を削除しました。")
                                        time.sleep(1)
                                        st.rerun()
                                        
                        st.markdown("---")
                        st.markdown("🗨️ **この商品への公開やり取り（コメント）**")
                        prod_comments = [c for c in all_comments if c["product_id"] == prod["id"]]
                        
                        if prod_comments:
                            for cm in prod_comments:
                                st.markdown(f"👤 **{cm['sender']}** ({cm['timestamp']}): {cm['message']}")
                        else:
                            st.caption("まだやり取りはありません。質問や購入希望を下に書き込んでみましょう。")
                        
                        with st.form(key=f"comment_form_{prod['id']}", clear_on_submit=True):
                            new_comment_msg = st.text_input("コメントを入力する", placeholder="例：これ購入したいです！", key=f"input_{prod['id']}")
                            submit_comment = st.form_submit_button("💬 コメントを送信")
                            
                            if submit_comment:
                                if not new_comment_msg:
                                    st.error("❌ コメント内容が空欄です。")
                                else:
                                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    c_data = {
                                        "action": "add_comment",
                                        "product_id": prod["id"],
                                        "sender": sender,
                                        "message": new_comment_msg,
                                        "timestamp": now_str
                                    }
                                    with st.spinner("🔄 コメントを送信中..."):
                                        res = requests.post(GAS_URL, data=json.dumps(c_data))
                                        if res.status_code == 200:
                                            st.success("✅ コメントを投稿しました！")
                                            time.sleep(1)
                                            st.rerun()

    # ==========================================
    # 💝 タブ2：感謝のJAY送金画面
    # ==========================================
    with tab2:
        st.subheader("🚀 JAYを送る・体験談をシェアする")
        receiver = st.selectbox("1. 誰に送りますか？", MEMBER_LIST, key="receiver_select")
        amount = st.number_input("2. 送るJAYの枚数を指定してください", min_value=0, value=10, step=10, key="send_amount")
        message = st.text_area("3. メッセージや、JWティーの体験談を自由に書いてください", placeholder="感謝の言葉をここに...", key="send_msg")

        if st.button("💝 感謝のJAYを送信する", use_container_width=True, key="send_btn"):
            if receiver == "選択してください":
                st.error("❌ 送る相手を選択してください。")
            elif sender == receiver:
                st.error("❌ 自分自身にJAYを送ることはできません。")
            elif amount <= 0:
                st.error("❌ 1 JAY以上の枚数を指定してください。")
            elif amount > current_balance:
                st.error(f"❌ 残高不足です。現在の残高（{current_balance} JAY）を超える送金はできません。")
            else:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data = {
                    "action": "send_jay",
                    "timestamp": now_str,
                    "sender": sender,
                    "receiver": receiver,
                    "amount": amount,
                    "message": message
                }
                with st.spinner("🔄 スプレッドシートに記録中..."):
                    res = requests.post(GAS_URL, data=json.dumps(data))
                    if res.status_code == 200:
                        st.success(f"🎉 送金完了！ {receiver} さんへ {amount} JAY を送信しました。")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
else:
    if sender != "選択してください":
        st.caption("🔒 正しい暗証番号を入力すると、掲示板や送金機能がここに表示されます。")