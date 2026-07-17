import streamlit as st
import pandas as pd
from datetime import datetime
import time
import streamlit.components.v1 as components
from supabase import create_client

# ==========================================
# 1. Supabase データベース接続設定
# ==========================================
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# 初期データの自動登録（テーブルが空の場合のみ実行）
def setup_initial_data():
    res = supabase.table("equip_items").select("name").limit(1).execute()
    if len(res.data) == 0:
        initial_data = []
        # ガラス道具 (10種)
        glass_items = ["シャンプーカバー", "シャンプーホルダー", "チャンネル20インチ", "チャンネル16インチ", "ハンドル", "カールコード", "洗剤容器", "ガラスカッター", "SSホルダー", "ヘルメット"]
        for g in glass_items:
            initial_data.append({"name": g, "stock": 0, "category": "ガラス道具", "threshold": 4, "last_checked": ""})
            
        # 制服 (41種)
        uniform_items = ["ジャンパー (LL)", "ジャンパー (L)", "ジャンパー (M)", "冬シャツ (5L)", "冬シャツ (4L)", "冬シャツ (LL)", "冬シャツ (L)", "冬シャツ (M)", "冬シャツ (S)", "ポロシャツ (LL)", "ポロシャツ (L)", "ポロシャツ (M)", "防寒着【上着】 (LL)", "防寒着【上着】 (L)", "防寒着【上着】 (M)", "防寒着【ズボン】 (3L)", "防寒着【ズボン】 (LL)", "防寒着【ズボン】 (L)", "防寒着【ズボン】 (M)", "雨合羽 (LL)", "雨合羽 (L)", "雨合羽 (M)", "ツナギ【長袖】 (3L)", "ツナギ【長袖】 (LL)", "ツナギ【長袖】 (L)", "ツナギ【長袖】 (M)", "ツナギ【半袖】 (3L)", "ツナギ【半袖】 (LL)", "ツナギ【半袖】 (L)", "ツナギ【半袖】 (M)", "ズボン (73)", "ズボン (76)", "ズボン (79)", "ズボン (82)", "ズボン (85)", "ズボン (88)", "ズボン (91)", "ズボン (95)", "ズボン (100)", "ズボン (105)", "ズボン (110)"]
        for u in uniform_items:
            initial_data.append({"name": u, "stock": 0, "category": "制服", "threshold": 5, "last_checked": ""})
        supabase.table("equip_items").insert(initial_data).execute()

setup_initial_data()

# ==========================================
# 2. DB操作関数群 
# ==========================================
def get_inventory(category=None):
    query = supabase.table("equip_items").select("*")
    if category:
        query = query.eq("category", category)
    response = query.execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        df = df.sort_values(by="name")
    return df

def process_action(staff_name, action, item_name, qty, comment):
    now = datetime.now()
    date_str = now.strftime("%Y/%m/%d")
    stock_diff = qty if action == "追加" else -qty
    staff_record = "会社購入" if action == "追加" else staff_name
        
    res = supabase.table("equip_items").select("stock").eq("name", item_name).execute()
    if res.data:
        current_stock = res.data[0]['stock']
        new_stock = current_stock + stock_diff
        supabase.table("equip_items").update({"stock": new_stock, "last_checked": date_str}).eq("name", item_name).execute()
    
    supabase.table("equip_history").insert({
        "date": date_str, "staff_name": staff_record, "item_name": item_name, 
        "action": action, "change_amount": qty, "comment": comment
    }).execute()

def delete_history_record(record_id, item_name, action, qty):
    stock_diff = qty if action == "支給" else -qty
    supabase.table("equip_history").delete().eq("id", record_id).execute()
    res = supabase.table("equip_items").select("stock").eq("name", item_name).execute()
    if res.data:
        current_stock = res.data[0]['stock']
        new_stock = current_stock + stock_diff
        supabase.table("equip_items").update({"stock": new_stock}).eq("name", item_name).execute()

# ==========================================
# 3. モダンUI・CSS設定
# ==========================================
st.set_page_config(page_title="在庫・貸出管理Pro", page_icon="🏢", layout="centered")

pro_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif !important; color: #1e293b; background-color: #f8fafc; }
div[data-testid="stForm"], .css-1r6slb0 { background-color: #ffffff; border-radius: 16px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03); border: 1px solid #e2e8f0; }
input, div[data-baseweb="select"] > div { background-color: #f1f5f9 !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; color: #334155 !important; transition: all 0.2s ease; }
input:focus, div[data-baseweb="select"] > div:focus-within { border-color: #3b82f6 !important; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important; }
div[data-testid="stNumberInput"] div[data-baseweb="base-input"] { position: relative !important; min-height: 4rem !important; overflow: hidden !important; display: flex !important; align-items: center !important; }
div[data-testid="stNumberInput"] input { font-size: 1.5rem !important; font-weight: 700 !important; padding-left: 1rem !important; padding-right: 8rem !important; height: 4rem !important; background: transparent !important; border: none !important; }
button[data-testid="stNumberInputStepDown"] { position: absolute !important; right: 4rem !important; width: 3.5rem !important; height: 85% !important; background-color: #3b82f6 !important; border-radius: 6px !important; margin: 0 !important; border: none !important; z-index: 10 !important; }
button[data-testid="stNumberInputStepUp"] { position: absolute !important; right: 0.2rem !important; width: 3.5rem !important; height: 85% !important; background-color: #ef4444 !important; border-radius: 6px !important; margin: 0 !important; border: none !important; z-index: 10 !important; }
button[data-testid="stNumberInputStepDown"] svg, button[data-testid="stNumberInputStepUp"] svg { fill: #ffffff !important; width: 1.5rem !important; height: 1.5rem !important; }
button[data-testid="baseButton-primary"] { background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important; border: none !important; border-radius: 10px !important; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important; padding: 0.75rem 1.5rem !important; transition: transform 0.1s ease, box-shadow 0.1s ease !important; }
button[data-testid="baseButton-primary"]:active { transform: translateY(2px) !important; box-shadow: 0 2px 6px rgba(37, 99, 235, 0.2) !important; }
button[data-testid="baseButton-primary"] p { color: #ffffff !important; font-weight: 700 !important; font-size: 1.1rem !important; }
@media print {
    @page { size: A4 portrait; margin: 15mm; }
    .no-print, section[data-testid="stSidebar"], button, header { display: none !important; }
    html, body, .main, .block-container { background: #fff !important; padding: 0 !important; margin: 0 !important; width: 100% !important; max-width: 100% !important; }
    #print-table { width: 100%; border-collapse: collapse; font-size: 11pt; margin-top: 20px; font-family: 'Noto Sans JP', sans-serif; }
    #print-table th, #print-table td { border: 1px solid #334155; padding: 8px 12px; text-align: left; }
    #print-table th { background-color: #f1f5f9; font-weight: bold; }
    h3 { margin-bottom: 5px !important; font-size: 18pt !important; }
}
</style>
"""
st.markdown(pro_css, unsafe_allow_html=True)

# ==========================================
# 4. サイドバー・ナビゲーション
# ==========================================
st.sidebar.markdown("<h2 style='text-align: center; color: #1e293b; margin-bottom: 30px;'>🏢 管理メニュー</h2>", unsafe_allow_html=True)

PAGES = {
    "📝 入力 (出入り記録)": "input",
    "📦 リアルタイム現在庫": "stock",
    "📚 貸出一覧 (履歴・印刷)": "history",
    "⚙️ 管理・修正機能": "admin"
}

if "page" not in st.session_state:
    st.session_state.page = "input"

for page_name, page_key in PAGES.items():
    if st.sidebar.button(page_name, use_container_width=True, type="primary" if st.session_state.page == page_key else "secondary"):
        st.session_state.page = page_key
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("© 2026 Inventory Pro")

# ==========================================
# 5. 各画面のロジック
# ==========================================
if st.session_state.page == "input":
    st.markdown("<h3>📝 道具・制服の出入り記録</h3>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🪟 ガラス道具", "👕 制服"])
    
    for tab, category, color_theme in zip([tab1, tab2], ["ガラス道具", "制服"], ["#e0f2fe", "#f3e8ff"]):
        with tab:
            st.markdown(f"<div style='background-color: {color_theme}; padding: 10px; border-radius: 8px; margin-bottom: 20px; font-weight: 700; color: #1e293b;'>{category}の入力フォーム</div>", unsafe_allow_html=True)
            df_items = get_inventory(category)
            item_list = df_items['name'].tolist() if not df_items.empty else []
            
            with st.form(key=f"form_{category}", clear_on_submit=True):
                col1, col2 = st.columns([1, 1])
                with col1:
                    action = st.radio("区分", ["支給", "追加"], horizontal=True, key=f"action_{category}")
                with col2:
                    if action == "支給":
                        staff = st.text_input("👤 スタッフ名 (必須)", key=f"staff_{category}")
                    else:
                        st.text_input("👤 スタッフ名", value="会社購入", disabled=True, key=f"staff_disabled_{category}")
                        staff = "会社購入"
                
                item = st.selectbox("品名を選択", item_list, key=f"item_{category}")
                qty = st.number_input("数量", min_value=1, value=1, step=1, key=f"qty_{category}")
                comment = st.text_input("備考 (任意)", placeholder="例: サイズ交換、破損による再支給など", key=f"comment_{category}")
                
                submit = st.form_submit_button("この内容で記録する", type="primary", use_container_width=True)
                
                if submit:
                    if action == "支給" and not staff.strip():
                        st.error("⚠️ 支給の場合はスタッフ名を入力してください。")
                    else:
                        process_action(staff, action, item, qty, comment)
                        st.toast(f"{item} を{qty}個 {action}として記録しました！", icon="✅")
                        time.sleep(1)
                        st.rerun()

elif st.session_state.page == "stock":
    st.markdown("<h3 class='no-print'>📦 リアルタイム現在庫</h3>", unsafe_allow_html=True)
    category = st.radio("表示カテゴリ", ["ガラス道具", "制服"], horizontal=True)
    df = get_inventory(category)
    
    if not df.empty:
        alerts = df[df['stock'] <= df['threshold']]
        is_alert_mode = st.checkbox(f"🚨 発注が必要なアイテムのみ表示 ({len(alerts)}件)", value=False)
        display_df = alerts if is_alert_mode else df
        
        display_df = display_df[['name', 'stock', 'threshold', 'last_checked']].copy()
        display_df.columns = ['品名', '現在庫', 'アラート基準', '最終更新日']
        display_df.set_index('品名', inplace=True)
        
        st.dataframe(
            display_df.style.apply(lambda x: ['background-color: #fee2e2' if v <= x['アラート基準'] else '' for v in x], subset=['現在庫'], axis=1),
            use_container_width=True
        )
        
        if is_alert_mode and not alerts.empty:
            st.markdown("---")
            today = datetime.now().strftime("%Y/%m/%d")
            lines = [f"【発注依頼】{today} ({category})"]
            for _, row in alerts.iterrows():
                lines.append(f"・{row['name']} (残り: {row['stock']} / 基準: {row['threshold']})")
            lines.append("上記の発注をお願いいたします。")
            share_text = "\\n".join(lines)
            
            btn_html = f"""
            <button onclick="navigator.share({{title: '発注リスト', text: '{share_text}'}}).catch(e=>alert('共有機能が非対応です。表をコピーしてください。'))" 
                style="background: #06C755; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%;">
                💬 LINE等で発注リストをシェアする
            </button>
            """
            components.html(btn_html, height=60)
    else:
        st.info("データがありません。")

elif st.session_state.page == "history":
    st.markdown("<h3 class='no-print'>📚 貸出・出入り履歴</h3>", unsafe_allow_html=True)
    res_hist = supabase.table("equip_history").select("*").order("id", desc=True).execute()
    res_items = supabase.table("equip_items").select("name, category").execute()
    
    df_hist = pd.DataFrame(res_hist.data)
    df_items = pd.DataFrame(res_items.data)
    
    if df_hist.empty or df_items.empty:
        st.info("履歴がありません。")
    else:
        df_hist = df_hist.merge(df_items, left_on="item_name", right_on="name", how="left")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            target_cat = st.radio("カテゴリ", ["ガラス道具", "制服"], horizontal=True)
        with col2:
            search_staff = st.text_input("🔍 スタッフ名検索")
        with col3:
            search_year = st.selectbox("📅 年指定", ["すべて"] + sorted(list(set([d[:4] for d in df_hist['date'] if isinstance(d, str)])), reverse=True))

        filtered = df_hist[df_hist['category'] == target_cat].copy()
        if search_staff:
            filtered = filtered[filtered['staff_name'].str.contains(search_staff, na=False)]
        if search_year != "すべて":
            filtered = filtered[filtered['date'].str.startswith(search_year)]
            
        if not filtered.empty:
            filtered = filtered[['date', 'staff_name', 'item_name', 'action', 'change_amount', 'comment']]
            filtered.columns = ['日付', '氏名', '道具名' if target_cat == "ガラス道具" else '制服名', '区分', '数量', '備考']
            
            print_mode = st.checkbox("🖨️ 印刷モード (A4・PDF用)")
            
            if print_mode:
                st.markdown("<div class='no-print' style='background: #d1e7dd; padding: 15px; border-radius: 8px; color: #0f5132; margin-bottom: 20px;'>Ctrl+P (または共有ボタン) から印刷・PDF保存を実行してください。</div>", unsafe_allow_html=True)
                table_html = filtered.to_html(index=False, escape=False)
                st.markdown(f"""
                <div id="print-table-wrapper">
                    <h3>{target_cat} 出入り履歴一覧</h3>
                    {table_html.replace('<table border="1" class="dataframe">', '<table id="print-table">')}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.dataframe(filtered, use_container_width=True, hide_index=True)
        else:
            st.warning("該当する履歴がありません。")

elif st.session_state.page == "admin":
    st.markdown("<h3>⚙️ 管理・履歴の修正</h3>", unsafe_allow_html=True)
    tab_master, tab_fix = st.tabs(["📝 マスターデータ管理", "🗑️ 履歴の修正 (誤操作取り消し)"])
    
    with tab_master:
        st.write("準備中：アイテムの追加や基準値の変更機能（※現状のデータでそのまま運用可能です）")
        
    with tab_fix:
        st.info("誤って入力してしまった履歴を安全に削除し、在庫数を元に戻します。")
        res_hist = supabase.table("equip_history").select("*").order("id", desc=True).limit(50).execute()
        df_hist = pd.DataFrame(res_hist.data)
        
        if not df_hist.empty:
            options = []
            for _, row in df_hist.iterrows():
                opt = f"[ID:{row['id']}] {row['date']} | {row['staff_name']} | {row['item_name']} | {row['action']} {row['change_amount']}個"
                options.append(opt)
                
            selected_record = st.selectbox("削除する履歴を選択 (直近50件)", options)
            record_id = int(selected_record.split("]")[0].replace("[ID:", ""))
            target_row = df_hist[df_hist['id'] == record_id].iloc[0]
            
            st.warning(f"以下の履歴を削除し、在庫数を再計算します。\n\n**{target_row['item_name']}** ({target_row['action']} {target_row['change_amount']}個)")
            
            confirm = st.checkbox("⚠️ 確認しました（この履歴を完全に削除します）")
            if confirm:
                if st.button("🚨 履歴を削除して在庫を戻す", type="primary"):
                    delete_history_record(record_id, target_row['item_name'], target_row['action'], target_row['change_amount'])
                    st.toast("履歴を削除し、在庫を修正しました。", icon="🗑️")
                    time.sleep(1.5)
                    st.rerun()