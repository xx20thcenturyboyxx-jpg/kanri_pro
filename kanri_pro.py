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

# ==========================================
# 2. DB操作関数
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

def get_staff_list():
    res = supabase.table("equip_items").select("name").eq("category", "スタッフ").execute()
    if not res.data:
        initial_staff = ["小垣武正", "森建一", "山口徹也", "小原眞和", "中嶋秀彦", "奥山将光", "澤田智紀", "鎌倉健二", "竹村悟史", "赤尾定治", "熊谷豊樹", "武内和寿", "田中裕一", "今阪唯木", "青山幸弘", "吉川智", "林直樹", "前田茂樹", "タワーズ"]
        insert_data = [{"name": s, "stock": 0, "category": "スタッフ", "threshold": 0, "last_checked": ""} for s in initial_staff]
        supabase.table("equip_items").insert(insert_data).execute()
        return initial_staff
    return [r['name'] for r in res.data]

STAFF_LIST = get_staff_list()

def process_action(staff_name, action, item_name, qty, comment):
    date_str = datetime.now().strftime("%Y/%m/%d")
    stock_diff = qty if action == "補充" else -qty
    res = supabase.table("equip_items").select("stock").eq("name", item_name).execute()
    if res.data:
        current_stock = res.data[0]['stock']
        new_stock = current_stock + stock_diff
        supabase.table("equip_items").update({"stock": new_stock, "last_checked": date_str}).eq("name", item_name).execute()
    supabase.table("equip_history").insert({
        "date": date_str, "staff_name": staff_name, "item_name": item_name, 
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
# 3. プロ仕様UI CSS
# ==========================================
pro_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body { font-family: 'Inter', sans-serif !important; background-color: #f8fafc; }
/* カード・表のデザイン */
.card-box { background: #ffffff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; margin-bottom: 16px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { background-color: #f1f5f9; padding: 10px; text-align: left; border-bottom: 2px solid #cbd5e1; }
td { padding: 10px; border-bottom: 1px solid #e2e8f0; }
/* 印刷用 */
@media print { .no-print, .stSidebar, .stRadio, button { display: none !important; } .main { padding: 0 !important; } table { border: 1px solid #000; } }
</style>
"""
st.markdown(pro_css, unsafe_allow_html=True)

# ==========================================
# 4. ナビゲーション・タイトル
# ==========================================
PAGES = ["📝 入力", "📦 在庫一覧", "📚 履歴", "⚙️ 管理"]
if "page" not in st.session_state: st.session_state.page = "📝 入力"

st.sidebar.markdown("## 🏢 管理メニュー")
for p in PAGES:
    if st.sidebar.button(p, use_container_width=True, type="primary" if st.session_state.page == p else "secondary"):
        st.session_state.page = p
        st.rerun()

st.markdown("### 🏢 備品・制服 貸出管理")
st.radio("メニュー", PAGES, horizontal=True, label_visibility="collapsed", key="page")

# ==========================================
# 5. 各画面ロジック
# ==========================================
if st.session_state.page == "📝 入力":
    tab1, tab2 = st.tabs(["👕 制服", "🪟 ガラス道具"])
    with tab1:
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        action_u = st.radio("区分", ["支給", "補充"], horizontal=True)
        # 【解決】エクスパンダーで名前選択（キーボード無効化）
        if action_u == "補充":
            st.text_input("👤 補充元", value="会社購入", disabled=True)
            staff_u = "会社購入"
        else:
            with st.expander("👤 支給するスタッフを選択"):
                staff_u = st.radio("スタッフ名", STAFF_LIST, label_visibility="collapsed")
        
        df_u = get_inventory("制服")
        base_types = sorted(list(set([name.split(" ")[0] for name in df_u['name'].tolist()])))
        selected_base = st.selectbox("種類", base_types)
        size_options = [n for n in df_u['name'].tolist() if n.startswith(selected_base)]
        item_u = st.radio("サイズ", size_options, horizontal=True)
        qty_u = st.number_input("数量", min_value=1, value=1, step=1)
        comment_u = st.text_input("備考")
        if st.button("記録する", type="primary", use_container_width=True):
            process_action(staff_u, action_u, item_u, qty_u, comment_u)
            st.success("完了しました！")
            time.sleep(0.5); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        action_g = st.radio("区分", ["支給", "補充"], horizontal=True)
        if action_g == "補充":
            st.text_input("👤 補充元", value="会社購入", disabled=True)
            staff_g = "会社購入"
        else:
            with st.expander("👤 支給するスタッフを選択"):
                staff_g = st.radio("スタッフ名", STAFF_LIST, label_visibility="collapsed")
        
        item_g = st.selectbox("品名", get_inventory("ガラス道具")['name'].tolist())
        qty_g = st.number_input("数量", min_value=1, value=1, step=1)
        if st.button("記録する", type="primary", use_container_width=True):
            process_action(staff_g, action_g, item_g, qty_g, "")
            st.success("完了しました！")
            time.sleep(0.5); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "📦 在庫一覧":
    category = st.radio("カテゴリ", ["制服", "ガラス道具"], horizontal=True)
    df = get_inventory(category)
    alerts = df[df['stock'] <= df['threshold']]
    
    col1, col2 = st.columns(2)
    with col1: is_alert = st.checkbox("🚨 不足分のみ表示")
    with col2: print_mode = st.checkbox("🖨️ A4印刷")
    
    display_df = (alerts if is_alert else df)[['name', 'stock', 'last_checked']]
    display_df.columns = ['商品', '在庫数', '最終確認']
    
    def highlight_alert(row):
        return ['background-color: #fee2e2; color: #991b1b; font-weight: bold;'] * len(row) if row['在庫数'] <= 2 else [''] * len(row)
    
    st.table(display_df.style.hide(axis="index").apply(highlight_alert, axis=1))
    
    if is_alert and not alerts.empty:
        share_text = "\\n".join([f"{row['name']}の在庫が不足しています。" for _, row in alerts.iterrows()])
        btn_html = f'<button onclick="navigator.share({{text: \'{share_text}\'}})" style="width:100%; padding:10px; background:#06C755; color:white; border:none; border-radius:8px; font-weight:bold;">💬 LINE等で発注依頼</button>'
        components.html(btn_html, height=50)

elif st.session_state.page == "📚 履歴":
    st.markdown("### 📚 履歴")
    res_hist = supabase.table("equip_history").select("*").order("date", desc=True).execute()
    df_hist = pd.DataFrame(res_hist.data)
    tab1, tab2 = st.tabs(["制服", "ガラス道具"])
    for tab, cat in zip([tab1, tab2], ["制服", "ガラス道具"]):
        with tab:
            df = df_hist[df_hist['item_name'].isin(get_inventory(cat)['name'].tolist())]
            staff_s = st.selectbox(f"氏名絞り込み({cat})", ["すべて"] + STAFF_LIST, key=cat)
            if staff_s != "すべて": df = df[df['staff_name'] == staff_s]
            st.table(df[['date', 'staff_name', 'item_name', 'action', 'change_amount']])

elif st.session_state.page == "⚙️ 管理":
    st.info("管理設定画面です。")
    # (既存の管理ロジック)
