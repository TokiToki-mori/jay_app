import streamlit as st
import requests
import datetime
import pandas as pd

# ページ設定
st.set_page_config(page_title="JAY コミュニティ通貨システム", page_icon="🪙", layout="centered")

# スタイリング
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #4CAF50; color: white; }
    .wallet-box { padding: 20px; border-radius: 10px; background-color: #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# 🔗 動作確認済みの最新GASウェブアプリURL（埋め込み済み）
GAS_URL = "https://script.google.com/macros/s/AKfycby_xMsvYyVBNDe4YgtDedDMuU_ph1_X1K0NyiVyyzNgqKNSo7uPciL_kZG4FUbcCxny/exec"

@st.cache_data(ttl=5)
def fetch_data():
    try:
        response = requests.get(GAS_URL)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"データ通信エラー: {e}")
    return {"members": [], "history": [], "products": [], "comments": []}

data = fetch_data()
members_list = data.get("members", [])
history_list = data.get("history", [])

# タイトル
st.title("🪙 JAY コミュニティ通貨")

# 1. ログイン処理
st.subheader("🔑 ログイン")
member_names = [m[0] for m in members_list]

if not member_names:
    st.warning("現在、会員名簿データが取得できていないか、空の状態です。GASのデプロイと権限（全員）を確認してください。")
    current_user = None
else:
    current_user = st.selectbox("あなたの名前を選択してください", member_names)

if current_user:
    # パスワード検証（名簿の3列目[2]にパスワードがある場合）
    user_info = next((m for m in members_list if m[0] == current_user), None)
    correct_pass = user_info[1] if (user_info and len(user_info) > 1) else ""
    
    if correct_pass:
        password_input = st.text_input("パスワードを入力してください", type="password")
        if password_input != str(correct_pass):
            st.error("パスワードが一致しません。")
            st.stop()
            
    # 残高の取得（名簿の4列目[2]、またはインデックス[2]に数値として格納されているもの）
    initial_balance = float(user_info[2]) if (user_info and len(user_info) > 2 and user_info[2] != "") else 0.0
    
    # 履歴から現在残高のリアルタイム計算
    incoming = sum(float(h["amount"]) for h in history_list if h["receiver"] == current_user)
    outgoing = sum(float(h["amount"]) for h in history_list if h["sender"] == current_user)
    current_balance = initial_balance + incoming - outgoing

    # 残高表示
    st.markdown(f"""
    <div class="wallet-box">
        <p style="margin-bottom:5px; color:#666;">現在のウォレット残高</p>
        <h2 style="margin:0; color:#2E7D32;">{int(current_balance):,} JAY</h2>
        <p style="margin:5px 0 0 0; font-size:0.8em; color:#999;">ベース初期値: {int(initial_balance):,} JAY</p>
    </div>
    """, unsafe_allow_html=True)

    # 2. 送金機能
    st.subheader("💸 JAYを送る")
    receivers = [name for name in member_names if name != current_user]
    
    if receivers:
        receiver = st.selectbox("送り先を選択してください", receivers)
        amount = st.number_input("送る数量 (JAY)", min_value=1, max_value=int(current_balance) if current_balance > 1 else 1, step=1)
        message = st.text_area("メッセージ（任意）", placeholder="お礼の言葉など")

        if st.button("送金を実行する"):
            if current_balance < amount:
                st.error("残高が不足しています。")
            else:
                payload = {
                    "action": "send_jay",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "sender": current_user,
                    "receiver": receiver,
                    "amount": amount,
                    "message": message
                }
                try:
                    res = requests.post(GAS_URL, json=payload)
                    if res.status_code == 200 and res.json().get("status") == "success":
                        st.success(f"{receiver} さんへ {amount} JAY の送金が完了しました！")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("送金処理に失敗しました。GAS側の出力を確認してください。")
                except Exception as e:
                    st.error(f"通信エラーが発生しました: {e}")
    else:
        st.info("あなた以外の会員が登録されていません。")

    # 3. 履歴表示
    st.subheader("📜 あなたの取引履歴")
    user_history = [h for h in history_list if h["sender"] == current_user or h["receiver"] == current_user]
    
    if user_history:
        formatted_history = []
        for h in reversed(user_history):
            dt = datetime.datetime.fromisoformat(h["timestamp"].replace("Z", "+00:00")).astimezone(None)
            date_str = dt.strftime("%Y/%m/%d %H:%M")
            
            if h["sender"] == current_user:
                type_str = "🛑 送金"
                partner = h["receiver"]
                amt_str = f"-{int(h['amount'])}"
            else:
                type_str = "🟢 受取"
                partner = h["sender"]
                amt_str = f"+{int(h['amount'])}"
                
            formatted_history.append({
                "日時": date_str,
                "種別": type_str,
                "取引相手": partner,
                "数量 (JAY)": amt_str,
                "メッセージ": h["message"]
            })
        st.dataframe(pd.DataFrame(formatted_history), use_container_width=True)
    else:
        st.text("取引履歴はまだありません。")