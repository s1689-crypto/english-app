import streamlit as st
import google.generativeai as genai
import pandas as pd

# ---------------------------------------------------------
# 1. アプリの設定
# ---------------------------------------------------------
st.set_page_config(page_title="AI英作文添削アプリ", page_icon="📝")
st.title("📝 AI英作文 添削アプリ")
st.write("条件を確認して、英作文に挑戦しましょう！")

# ==========================================
# ★ここに「ウェブに公開(CSV)」のURLを貼る★
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQE_VETaSm_um88Tu8pcF5zN9Ec1DuQ2i-RlBk3No1iTDQKbsVFR39lG-X0811ymyz3mqcGtOEeg_lc/pub?gid=0&single=true&output=csv"
# ==========================================

# ---------------------------------------------------------
# 2. APIキーの準備
# ---------------------------------------------------------
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Google APIキー", type="password")

# ---------------------------------------------------------
# 3. データ読み込み
# ---------------------------------------------------------
@st.cache_data(ttl=600)
def load_data(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        df = df.fillna("なし")
        df = df.astype(str)
        return df
    except Exception as e:
        return str(e)

if st.sidebar.button("🔄 お題を最新に更新"):
    st.cache_data.clear()
    st.rerun()

data = load_data(SHEET_URL)

if isinstance(data, str):
    st.error("❌ データの読み込みに失敗しました。")
    st.error(f"エラー詳細: {data}")
    st.stop()

df = data
required_cols = ["学年", "お題", "配点", "語数指定", "条件1", "条件2", "条件3", "評価規準"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"エラー: 以下の列が足りません: {missing}")
    st.stop()

# ---------------------------------------------------------
# 4. メニュー選択
# ---------------------------------------------------------
grades = df['学年'].unique()
selected_grade = st.selectbox("▼ 学年を選んでください", grades)

grade_data = df[df['学年'] == selected_grade]
topics = grade_data['お題'].unique()
selected_topic = st.selectbox("▼ お題を選んでください", topics)

row = grade_data[grade_data['お題'] == selected_topic].iloc[0]

score_max = row['配点']
word_limit = row['語数指定']
condition1 = row['条件1']
condition2 = row['条件2']
condition3 = row['条件3']
criteria = row['評価規準']

# ---------------------------------------------------------
# 5. 問題情報の表示
# ---------------------------------------------------------
st.divider()
st.subheader(f"お題：{selected_topic}")
st.markdown(f"**【配点】 {score_max}点 満点**")

if word_limit != "なし" and word_limit != "":
    st.info(f"**📏 語数指定:** {word_limit}")

conditions = []
if condition1 != "なし" and condition1 != "": conditions.append(condition1)
if condition2 != "なし" and condition2 != "": conditions.append(condition2)
if condition3 != "なし" and condition3 != "": conditions.append(condition3)

if conditions:
    st.warning("**⚠️ 指定条件:**\n" + "\n".join([f"- {c}" for c in conditions]))

st.divider()

# ---------------------------------------------------------
# 6. 入力エリア
# ---------------------------------------------------------
user_text = st.text_area("ここに英文を入力してください", height=200)

if user_text:
    word_count = len(user_text.split())
    st.caption(f"現在の語数: **{word_count}語**")
else:
    word_count = 0

# ---------------------------------------------------------
# ★修正点：Gemini 1.5 Flash を「強制指名」★
# もう自動検出機能は削除しました。これしか使いません。
# ---------------------------------------------------------
if st.button("採点・添削する"):
    if not api_key:
        st.error("APIキーが設定されていません。")
    elif not user_text:
        st.warning("英文を入力してください。")
    else:
        try:
            genai.configure(api_key=api_key)
            
            # 【ここが最重要】
            # 余計なことはせず、無料枠最強の "gemini-1.5-flash" だけを使います。
            # "gemini-3-pro" などが勝手に選ばれる余地をなくしました。
            model = genai.GenerativeModel("gemini-1.5-flash")
                
            cond_str = ", ".join(conditions) if conditions else "特になし"
                
            prompt = f"""
            あなたは英語教師です。以下のテスト問題を採点してください。
            【問題情報】学年:{selected_grade}, お題:{selected_topic}, 満点:{score_max}, 語数指定:{word_limit}, 指定条件:{cond_str}
            【生徒データ】語数:{word_count}語 (正確な値)
            【評価規準】{criteria}
            【指示】
            1. 語数指定・条件を守れていない場合は減点。
            2. {score_max}点満点で採点。
            3. 日本語で解説。
            
            【出力形式】
            ## 📊 採点結果: [点数] / {score_max} 点
            ## 📝 判定
            ・語数: {word_count}語 ({'OK' if word_limit == 'なし' else '[判定]'})
            ・条件: {'OK' if cond_str == '特になし' else '[判定]'}
            ## 🎯 修正
            [修正英文]
            ## 💡 解説
            [フィードバック]
            ---
            【生徒の英文】
            {user_text}
            """
            
            with st.spinner("Gemini 1.5 Flash が採点中..."):
                response = model.generate_content(prompt)
            
            st.success("採点完了！")
            st.markdown(response.text)

        except Exception as e:
            # エラー表示
            st.error("エラーが発生しました。")
            
            # もし「Not Found」系ならrequirements.txtの問題
            if "404" in str(e) or "not found" in str(e).lower():
                st.warning("⚠️ 重要: アプリの再起動が必要です！")
                st.info("画面右上の「Manage app」から「Reboot App」を押してください。")
            
            # もし「429」系なら使いすぎ（このコードなら出ないはずですが念のため）
            elif "429" in str(e):
                 st.warning("⚠️ 少し時間を置いてから再試行してください。")
            
            st.code(str(e))