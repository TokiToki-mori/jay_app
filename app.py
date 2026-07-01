import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json
import time
import base64

# 1. ページの設定
st.set_page_config(page_title="JAY コミュニティアプリ", page_icon="🪙", layout="centered")

# 🔗 モリケンタロウさんの最新動作確認済みGAS URL
GAS_URL = "https://script.google.com/macros/s/AKfycby_xMsvYyVBNDe4YgtDedDMuU_ph1_X1K0NyiVyyzNgqKNSo7uPciL_kZG4FUbcCxny/exec"

# 🎨 モリケンタロウさんのJAY公式イラストのBase64完全テキストデータ
DEFAULT_JAY_IMAGE = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAQAAAAEAAQMAAABFGoRRAAAABlBMVEUAAAD///+l2Z/dAAABi0lEQVR42u3YMWoDMRRG4X9AY8idI2SrkC1Cto7gEewieIsQLsI6gjewZcolZKuQrSNoK89gGstAAnmBwSg2SGlmXvX09Iskb96vE6KgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKDgX8GfB9m7z/N8v98vshvL0vV6bW3YMWoDMRRG4X9AY8idI2SrkC1Cto7gEewieIsQLsI6gjewZcolZKuQrSNoK89gGstAAnmBwSg2SGlmXvX09Iskb96vE6KgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKDgX8GfB9m7z/N8v98vshvL0vV6bW3NfR6GZbeWpff7/ZidWw6S7M6ymI/j2m4si9m7tSzm/b7O7ixL9+777L6TfXicXVuWHmffZg+Ww9Y+PE6fF8f+MvT2MHyevR8eh8eX7NPjw8vN7MvLy+z2wSfs3YNP2Xv7XbA3D/6wN7bfpZ777XftV7Ffvv0v9vO/v3Lw+Rvsf7Ff/v66h8fFfvn57b/vFvvf4P9uD8vNfvn27f9uD8vNfvn27f9uD8vNfvn27f9uD8vNfvn27f9uD8vNfvn27f9uD8vNfvn27f9uD8vNfvn27f9uD8vNfvn27f9uD8vNfvn2+X9jDcrNfvn379n+3h+Vmv3z79m8Py81++fZvD8vNfvn27V+yn/Zf9mZ7f3b++9p3wYKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKC/wZf8w9RshvL0n0AiK9oFovvWwIAAAAASUVORK5CYII="

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
# 👤 【生データ完全準拠版】インデックス修正ロジック
# ==========================================
raw_members = all_data.get("members", [])
MEMBER_LIST = ["選択してください"]
PASSWORD_DICT = {}
BALANCE_DICT = {} 

for m in raw_members:
    if isinstance(m, list) and len(m) >= 1:
        name = str(m[0]).strip()
        
        # 名前が有効な場合のみ処理
        if name and name != "" and name != "undefined" and name != "選択してください":
            MEMBER_LIST.append(name)
            
            # 暗証番号（m[1]）を厳密に取得
            if len(m) >= 2 and m[1] is not None and str(m[1]).strip() != "":
                PASSWORD_DICT[name] = str(m[1]).strip().split('.')[0].zfill(4)
            else:
                PASSWORD_DICT[name] = "NONE_PASSWORD"
                
            # 残高（m[2]）を厳密に取得
            if len(m) >= 3 and m[2] is not None:
                try:
                    BALANCE_DICT[name] = int(float(str(m[2]).strip()))
                except ValueError:
                    BALANCE_DICT[name] = 0
            else:
                BALANCE_DICT[name] = 0

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
    correct_password = PASSWORD_DICT.get(sender, "NONE_PASSWORD")
    
    input_password = st.text_input("🔑 4桁の暗証番号（誕生日など）を入力してください", type="password", max_chars=4)
    
    if input_password:
        if correct_password != "NONE_PASSWORD" and input_password.strip().zfill(4) == correct_password:
            authenticated = True
            current_balance = BALANCE_DICT.get(sender, 0)
            st.success(f"🔓 認証成功！ {sender} さんとしてログインしました。")
            st.info(f"💰 **現在の所持残高: {current_balance} JAY**")
        else:
            st.error("❌ 暗証番号が一致しないか、アカウントが正しく登録されていません。")
else:
    st.warning("⚠️ 最初にお名前を選択してください。選択するまで以下の機能は利用できません。")

st.markdown("---")

# 認証が成功している場合のみ、送金・掲示板を表示
if authenticated:
    current_balance = BALANCE_DICT.get(sender, 0)
    
    tab1, tab2 = st.tabs(["🏪 コミュニティ掲示板", "💝 感謝のJAY送金"])

    # ==========================================
    # 🏪 タブ1：コミュニティ掲示板画面
    # ==========================================
    with tab1:
        if "menu_index" not in st.session_state:
            st.session_state.menu_index = 0
            
        bazaar_mode = st.radio(
            "メニューを選んでください", 
            ["📦 出品されている商品を見る", "➕ 新しい商品・サービスを出品する"], 
            index=st.session_state.menu_index,
            horizontal=True
        )
        
        if bazaar_mode == "➕ 新しい商品・サービスを出品する":
            st.subheader("📝 新しい内容を掲示板に投稿する")
            
            prod_title = st.text_input("タイトル（投稿名）", placeholder="例：無農薬の新タマネギ譲ります！ / 草むしり手伝ってください")
            
            prod_category = st.selectbox("カテゴリ", [
                "🟢 出品（モノ・サービスを譲る/売る）", 
                "🔵 HELP（困りごと・手伝ってほしい）", 
                "✨ そういえば（JWティー体験談・気づき）"
            ])
            
            prod_desc = st.text_area("詳しい内容・提供可能日時など", placeholder="詳細を自由に詳しく書いてください。")
            
            if prod_category == "✨ そういえば（JWティー体験談・気づき）":
                st.info("💡 「そういえば（JWティー体験談）」の投稿感謝ボーナスとして、投稿完了時に自動で **100 JAY** があなたの残高に付与され、コメント欄に事務局からのメッセージが自動投稿されます！")
                prod_price = 0
                prod_delivery = "なし"
                prod_delivery_detail = "なし"
            else:
                prod_price = st.number_input("必要なJAY", min_value=0, value=100, step=50)
                prod_delivery = st.selectbox("受け渡し方法", ["手渡し", "郵送", "オンライン"])
                prod_delivery_detail = st.text_area("受け渡しの詳細", placeholder="例：山口市内の〇〇駅周辺で手渡し希望です。など")
            
            uploaded_file = st.file_uploader("写真をアップロード（JPEG/PNG）", type=["jpg", "jpeg", "png"])
            
            if st.button("🚀 この内容で掲示板に出品する", use_container_width=True):
                if not prod_title:
                    st.error("❌ タイトルを入力してください。")
                else:
                    final_image_string = DEFAULT_JAY_IMAGE
                    
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
                    
                    with st.spinner("🔄 スプレッドシートに情報を記録中..."):
                        res = requests.post(GAS_URL, data=json.dumps(data))
                        if res.status_code == 200:
                            st.success("🎉 掲示板への投稿が完了しました！")
                            st.balloons()
                            
                            if prod_category == "✨ そういえば（JWティー体験談・気づき）":
                                try:
                                    latest_data = requests.get(GAS_URL).json()
                                    latest_products = latest_data.get("products", [])
                                    if latest_products:
                                        my_posts = [p for p in latest_products if p["sender"] == sender]
                                        if my_posts:
                                            target_prod_id = my_posts[-1]["id"]
                                            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                            
                                            comment_data = {
                                                "action": "add_comment",
                                                "product_id": target_prod_id,
                                                "sender": "Jay事務局",
                                                "message": "素晴らしい気づきの投稿ありがとうございます！100JAYを事務局からプレゼントします！",
                                                "timestamp": now_str
                                            }
                                            requests.post(GAS_URL, data=json.dumps(comment_data))
                                except Exception:
                                    pass
                            
                            time.sleep(2)
                            st.session_state.menu_index = 0
                            st.rerun()
        else:
            st.session_state.menu_index = 1
            
            st.subheader("💬 投稿一覧")
            
            if not all_products:
                st.info("現在、掲示板に投稿はありません。最初の投稿をしてみましょう！")
            else:
                for prod in reversed(all_products):
                    with st.expander(f"【{prod['status']}】 {prod['title']} （投稿：{prod['sender']}さん）", expanded=True):
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            img_url = prod.get('image_url', '')
                            if isinstance(img_url, str) and (img_url.startswith("http") or img_url.startswith("data:image")) and "imgur.com" not in img_url and "drive.google.com" not in img_url:
                                try:
                                    st.image(img_url, use_container_width=True)
                                except Exception:
                                    st.image(DEFAULT_JAY_IMAGE, use_container_width=True)
                            else:
                                st.image(DEFAULT_JAY_IMAGE, use_container_width=True)
                                
                        with col2:
                            st.markdown(f"**🏷️ カテゴリ:** {prod['category']}")
                            if "そういえば" not in prod['category']:
                                st.markdown(f"**🪙 必要JAY:** {prod['amount']} JAY")
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
                            
                            if st.button("📝 上記の変更を反映する", key=f"save_{prod['id']}", use_container_width=True):
                                u_data = {
                                    "action": "update_product",
                                    "product_id": prod["id"],
                                    "amount": new_price,
                                    "status": new_status
                                }
                                with st.spinner("🔄 情報を更新中..."):
                                    res = requests.post(GAS_URL, data=json.dumps(u_data))
                                    if res.status_code == 200:
                                        st.success("✅ 情報を更新しました！")
                                        time.sleep(1)
                                        st.rerun()
                                        
                            if delete_btn:
                                d_data = {
                                    "action": "delete_product",
                                    "product_id": prod["id"]
                                }
                                with st.spinner("🗑️ 投稿を削除中..."):
                                    res = requests.post(GAS_URL, data=json.dumps(d_data))
                                    if res.status_code == 200:
                                        st.success("💥 投稿を削除しました。")
                                        time.sleep(1)
                                        st.rerun()
                                        
                        st.markdown("---")
                        st.markdown("🗨️ **この投稿への公開やり取り（コメント）**")
                        prod_comments = [c for c in all_comments if c["product_id"] == prod["id"]]
                        
                        if prod_comments:
                            for cm in prod_comments:
                                if cm['sender'] == "Jay事務局":
                                    st.markdown(f"📢 **{cm['sender']}** ({cm['timestamp']}): **{cm['message']}**")
                                else:
                                    st.markdown(f"👤 **{cm['sender']}** ({cm['timestamp']}): {cm['message']}")
                        else:
                            st.caption("まだやり取りはありません。質問やメッセージを下に書き込んでみましょう。")
                        
                        with st.form(key=f"comment_form_{prod['id']}", clear_on_submit=True):
                            new_comment_msg = st.text_input("コメントを入力する", placeholder="例：お話し聞いてみたいです！", key=f"input_{prod['id']}")
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
        message = st.text_area("3. メッセージや、JWティーの体験談を自由に書いてください", placeholder="感謝の言葉や、追加配布の理由などをここに...", key="send_msg")

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