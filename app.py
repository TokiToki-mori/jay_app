import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json
import time
import base64

# 1. ページの設定
st.set_page_config(page_title="JAY コミュニティアプリ", page_icon="🪙", layout="centered")

# 🔗 モリケンタロウさんの最新GASのURL
GAS_URL = "https://script.google.com/macros/s/AKfycbx5rmJBSnX6FNs3FSL4bbxIrSppmI9ksrT00Q2RYQSM7tHu6AHzfBXL8wUF8y3yaho/exec"

# 💰 全員の初期持ちJAY数
INITIAL_JAY = 1000

# 📊 Googleスプレッドシートからすべてのデータを一括で取得する関数
def get_all_data():
    try:
        response = requests.get(GAS_URL)
        if response.status_code == 200:
            return response.json()
        return {"members": ["選択してください"], "history": [], "products": [], "comments": []}
    except Exception:
        return {"members": ["選択してください"], "history": [], "products": [], "comments": []}

# 📊 残高を計算する関数
def get_current_balance(user_name, history):
    if user_name == "選択してください":
        return 0
    balance = INITIAL_JAY
    for log in history:
        if log["sender"] == user_name:
            balance -= log["amount"]
        if log["receiver"] == user_name:
            balance += log["amount"]
    return balance

# 🔄 最初に一括で全データを読み込む
all_data = get_all_data()
MEMBER_LIST = all_data.get("members", ["選択してください"])
all_history = all_data.get("history", [])
all_products = all_data.get("products", [])
all_comments = all_data.get("comments", [])

# --- 画面全体のタイトル ---
st.title("✨ コミュニティ通貨 JAY 総合システム")
st.write("感謝の送金と、メンバー同士の商品・サービスバザールを循環させましょう。")

st.markdown("---")

# ==========================================
# 👤 メイン画面の一番上にログイン配置
# ==========================================
st.subheader("👤 あなたのお名前を選択してください")
sender = st.selectbox("お名前を選ぶと、残高確認や投稿・コメントができるようになります", MEMBER_LIST, key="global_user", label_visibility="collapsed")

if sender != "選択してください":
    current_balance = get_current_balance(sender, all_history)
    st.info(f"💰 **{sender} さんの現在の所持残高: {current_balance} JAY**")
else:
    st.warning("⚠️ 最初にお名前を選択してください。選択するまで以下の機能は利用できません。")

st.markdown("---")

# 🗂️ 【★順序入れ替え改良】掲示板を第1タブ、送金を第2タブに設定
tab1, tab2 = st.tabs(["🏪 JAY商品バザール掲示板", "💝 感謝のJAY送金"])

# ==========================================
# 🏪 タブ1：JAY商品バザール掲示板画面（最初に表示されます）
# ==========================================
with tab1:
    bazaar_mode = st.radio("メニューを選んでください", ["📦 出品されている商品を見る", "➕ 新しい商品・サービスを出品する"], horizontal=True)
    
    # --- 🟢 モードA：商品を出品する画面 ---
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
            if sender == "選択してください":
                st.error("❌ 画面上部であなたのお名前を選択してください。")
            elif not prod_title:
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

    # --- 🔵 モードB：みんなの商品を見る画面 ---
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
                            if sender == "選択してください":
                                st.error("❌ 画面上部でお名前を選択してから書き込んでください。")
                            elif not new_comment_msg:
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
        if sender == "選択してください":
            st.error("❌ 画面上部であなたのお名前を選択してください。")
        elif receiver == "選択してください":
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