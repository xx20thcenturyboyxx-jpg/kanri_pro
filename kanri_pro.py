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
# 2. DB操作 & 独自UI関数
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

# 自動で閉じるスマート選択メニュー
def auto_close_selector(label, options, key, horizontal=True):
    if not options:
        options = ["データなし"]
        
    val_key = f"val_{key}"
    open_key = f"open_{key}"
    
    if val_key not in st.session_state:
        st.session_state[val_key] = options[0]
    elif st.session_state[val_key] not in options:
        st.session_state[val_key] = options[0]
        
    if open_key not in st.session_state:
        st.session_state[open_key] = False

    btn_label = f"{label} ｜ {st.session_state[val_key]}"
    if st.button(btn_label, key=f"btn_{key}", use_container_width=True):
        st.session_state[open_key] = not st.session_state[open_key]
        
    if st.session_state[open_key]:
        widget_key = f"wid_{key}"
        st.session_state[widget_key] = st.session_state[val_key]
        
        def on_change():
            st.session_state[val_key] = st.session_state[widget_key]
            st.session_state[open_key] = False
            
        st.radio("選択", options, key=widget_key, on_change=on_change, label_visibility="collapsed", horizontal=horizontal)
        
    return st.session_state[val_key]

# ==========================================
# 3. 超・プロ仕様 SaaSデザイン CSS (初代の美しいデザイン復刻版)
# ==========================================
st.set_page_config(page_title="在庫・貸出管理", layout="centered", initial_sidebar_state="expanded")

pro_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { 
    font-family: 'Inter', "Hiragino Sans", "Meiryo", sans-serif !important; 
    background-color: #f8fafc !important; 
    color: #0f172a !important; 
}
.block-container { padding-top: 2rem !important; }

/* 🌟 右上の「Fork」などの不要メニューを消去（スマホのサイドバー開閉ボタンは残す） */
[data-testid="stToolbar"],
.stAppDeployButton,
.stDeployButton,
#MainMenu {
    display: none !important;
}
header[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* 初代SaaSデザイン：メインメニューの美しいカプセル型デザイン */
div[data-testid="stRadio"] > div[role="radiogroup"] { 
    display: inline-flex; 
    flex-wrap: wrap; 
    gap: 4px; 
    background: #e2e8f0; 
    padding: 6px; 
    border-radius: 999px;
    margin-bottom: 24px; 
}
div[data-testid="stRadio"] label { 
    background-color: transparent; 
    padding: 8px 20px !important; 
    border-radius: 999px; 
    cursor: pointer; 
    transition: all 0.2s ease; 
    border: none; 
}
div[data-testid="stRadio"] label[data-checked="true"] { 
    background-color: #ffffff; 
    box-shadow: 0 2px 4px rgba(0,0,0,0.08); 
    color: #0f172a; 
    font-weight: 700; 
}

/* 入力エリア等のラジオボタン (独立した綺麗なボタン) */
div[data-testid="stTabs"] div[data-testid="stRadio"] > div[role="radiogroup"],
div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex;
    background: transparent !important;
    padding: 0 !important;
    margin-bottom: 16px;
    gap: 8px;
}
div[data-testid="stTabs"] div[data-testid="stRadio"] label,
div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stRadio"] label {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    padding: 10px 16px !important;
    border-radius: 8px !important;
    margin: 0 !important;
    flex: 1 1 auto;
    min-width: 80px;
    justify-content: center;
}
div[data-testid="stTabs"] div[data-testid="stRadio"] label[data-checked="true"],
div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stRadio"] label[data-checked="true"] {
    background-color: #eff6ff;
    border-color: #3b82f6;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    color: #1d4ed8;
}

/* 初代SaaSデザイン：カード（枠）の洗練された影と角丸 */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff;
    border-radius: 16px !important;
    padding: 24px !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.025) !important;
    border: 1px solid #f1f5f9 !important;
    margin-bottom: 20px !important;
}

/* プライマリーボタン（送信・記録）の高級グラデーション */
button[data-testid="baseButton-primary"] {
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    padding: 0.75rem 1rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    transition: all 0.2s ease !important;
}
button[data-testid="baseButton-primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important;
    background: linear-gradient(180deg, #334155 0%, #1e293b 100%) !important;
}

/* セカンダリーボタン（アコーディオン） */
button[data-testid="baseButton-secondary"] { 
    background-color: #ffffff !important; 
    border: 1px solid #cbd5e1 !important; 
    color: #334155 !important; 
    font-weight: 500 !important; 
    border-radius: 8px !important; 
    padding: 12px 16px !important; 
    display: flex !important;
    justify-content: flex-start !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
}
button[data-testid="baseButton-secondary"]:hover { 
    border-color: #94a3b8 !important; 
    background-color: #f8fafc !important; 
}
button[data-testid="baseButton-secondary"] p {
    font-size: 15px !important;
    margin: 0 !important;
    text-align: left !important;
    width: 100% !important;
}

/* テーブル（表） */
table { 
    width: 100%; 
    border-collapse: separate; 
    border-spacing: 0;
    font-size: 14px; 
    background-color: #ffffff; 
    border-radius: 8px; 
    overflow: hidden; 
    border: 1px solid #e2e8f0;
}
th { 
    background-color: #f8fafc; 
    padding: 14px 16px; 
    text-align: left; 
    border-bottom: 1px solid #e2e8f0; 
    color: #64748b;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
td { 
    padding: 14px 16px; 
    border-bottom: 1px solid #f1f5f9; 
    color: #334155;
}
tr:last-child td { border-bottom: none; }
tr:hover td { background-color: #f8fafc; }

h3, h4, h5 { color: #0f172a; font-weight: 700; letter-spacing: -0.025em; }

/* A4印刷用 */
@media print { 
    @page { size: A4 portrait; margin: 6mm; } 
    .no-print, section[data-testid="stSidebar"], header[data-testid="stHeader"], div[data-testid="stRadio"], div[data-testid="stCheckbox"], button { display: none !important; } 
    html, body, .main, .block-container { background: #fff !important; padding: 0 !important; margin: 0 !important; width: 100% !important; max-width: 100% !important; } 
    
    #print-area { width: 100%; color: #000; }
    #print-area table { border: 1px solid #334155; width: 100%; border-collapse: collapse; margin-bottom: 0px; border-radius: 0; } 
    #print-area th { background-color: #f1f5f9 !important; font-weight: bold; border: 1px solid #334155 !important; -webkit-print-color-adjust: exact; color: #000; letter-spacing: normal; text-transform: none; }
    #print-area td { border: 1px solid #334155 !important; }
    
    .print-glass table { font-size: 11pt; margin-top: 5px; }
    .print-glass th, .print-glass td { padding: 6px; }
    
    .print-uniform { font-size: 8pt; } 
    .masonry-layout { column-count: 2; column-gap: 12px; margin-top: 3px; }
    .group-wrapper { break-inside: avoid; page-break-inside: avoid; margin-bottom: 5px; } 
    .print-uniform th, .print-uniform td { padding: 2px 3px !important; line-height: 1.1; } 
    #print-area h3 { font-size: 11pt; margin: 0 0 3px 0; padding-bottom: 1px; border-bottom: 1px solid #334155; }
    #print-area h4 { margin: 0 0 1px 0; font-size: 8.5pt; color: #1e293b; }
}
</style>
"""
st.markdown(pro_css, unsafe_allow_html=True)

# ==========================================
# 4. ナビゲーション・タイトル
# ==========================================
PAGES = ["入力", "在庫一覧", "履歴", "管理"]
if "page" not in st.session_state: 
    st.session_state.page = "入力"

st.sidebar.markdown("<h2 style='text-align: center; color: #1e293b; margin-bottom: 30px; font-weight: 700;'>Inventory Pro</h2>", unsafe_allow_html=True)
for p in PAGES:
    if st.sidebar.button(p, use_container_width=True, type="primary" if st.session_state.page == p else "secondary"):
        st.session_state.page = p
        st.rerun()

st.markdown("<div class='no-print'><h3 style='margin-top: -30px; margin-bottom: 15px;'>備品・制服 貸出管理</h3></div>", unsafe_allow_html=True)
st.radio("メニュー", PAGES, horizontal=True, label_visibility="collapsed", key="page")

# ==========================================
# 5. 各画面ロジック
# ==========================================

# ----------------- 入力ページ -----------------
if st.session_state.page == "入力":
    tab1, tab2 = st.tabs(["制服", "ガラス道具"])
    
    with tab1:
        with st.container(border=True):
            action_u = st.radio("区分", ["支給", "補充"], horizontal=True, key="action_u")
            
            if action_u == "補充":
                st.text_input("補充元", value="会社購入", disabled=True, key="staff_add_u")
                staff_u = "会社購入"
            else:
                staff_u = auto_close_selector("スタッフ", STAFF_LIST, "staff_give_u")
            
            df_u = get_inventory("制服")
            if not df_u.empty:
                base_types = sorted(list(set([name.split(" ")[0] for name in df_u['name'].tolist()])))
                selected_base = auto_close_selector("種類", base_types, "base_u")
                
                size_options = [n for n in df_u['name'].tolist() if n.startswith(selected_base)]
                
                st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                item_u = st.radio("サイズを選択", size_options, horizontal=True, key="item_u")
            else:
                item_u = st.selectbox("品名を選択", ["データなし"], key="item_u_empty")
                
            qty_u = st.number_input("数量", min_value=1, value=1, step=1, key="qty_u")
            comment_u = st.text_input("備考", key="comment_u")
            
            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
            if st.button("この内容で記録する", type="primary", use_container_width=True, key="btn_u"):
                process_action(staff_u, action_u, item_u, qty_u, comment_u)
                st.success("記録が完了しました。")
                time.sleep(0.5)
                st.rerun()
    
    with tab2:
        with st.container(border=True):
            action_g = st.radio("区分", ["支給", "補充"], horizontal=True, key="action_g")
            
            if action_g == "補充":
                st.text_input("補充元", value="会社購入", disabled=True, key="staff_add_g")
                staff_g = "会社購入"
            else:
                staff_g = auto_close_selector("スタッフ", STAFF_LIST, "staff_give_g")
            
            df_g = get_inventory("ガラス道具")
            item_list_g = df_g['name'].tolist() if not df_g.empty else []
            item_g = auto_close_selector("品名", item_list_g, "item_g")
            
            qty_g = st.number_input("数量", min_value=1, value=1, step=1, key="qty_g")
            comment_g = st.text_input("備考", key="comment_g")
            
            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
            if st.button("この内容で記録する", type="primary", use_container_width=True, key="btn_g"):
                process_action(staff_g, action_g, item_g, qty_g, comment_g)
                st.success("記録が完了しました。")
                time.sleep(0.5)
                st.rerun()

# ----------------- 在庫一覧ページ -----------------
elif st.session_state.page == "在庫一覧":
    category = st.radio("カテゴリ", ["制服", "ガラス道具"], horizontal=True, key="inv_cat")
    df = get_inventory(category)
    
    if not df.empty:
        alerts = df[df['stock'] <= df['threshold']]
        
        col1, col2 = st.columns(2)
        with col1: 
            is_alert = st.checkbox("不足分のみ表示 (要発注)", key="inv_alert")
        with col2: 
            print_mode = st.checkbox("A4印刷モード", key="inv_print")
        
        display_df = (alerts if is_alert else df)[['name', 'stock', 'last_checked']]
        display_df.columns = ['商品', '在庫数', '最終確認']
        
        def highlight_alert(row):
            original_row = df[df['name'] == row['商品']].iloc[0]
            if row['在庫数'] <= original_row['threshold']:
                return ['background-color: #fee2e2; color: #991b1b; font-weight: bold;'] * len(row)
            return [''] * len(row)
        
        if print_mode:
            st.markdown("<div class='no-print' style='background: #f1f5f9; padding: 15px; border-radius: 8px; color: #334155; margin-bottom: 20px; font-weight: 500;'>Ctrl+P (スマホの場合は共有ボタン) から印刷を実行してください。</div>", unsafe_allow_html=True)
            
            today_str = datetime.now().strftime("%Y年%m月%d日")
            
            if category == "ガラス道具":
                html_table = "<table><thead><tr><th>商品</th><th>在庫数</th><th>最終確認</th></tr></thead><tbody>"
                for _, row in display_df.iterrows():
                    original_row = df[df['name'] == row['商品']].iloc[0]
                    is_alert_row = row['在庫数'] <= original_row['threshold']
                    bg = "background-color: #fee2e2; font-weight: bold;" if is_alert_row else ""
                    last_check = row['最終確認'] if pd.notna(row['最終確認']) else ""
                    html_table += f"<tr style='{bg}'><td>{row['商品']}</td><td style='text-align:center;'>{row['在庫数']}</td><td>{last_check}</td></tr>"
                html_table += "</tbody></table>"
                
                print_html = f"""
                <div id="print-area" class="print-glass">
                    <h3>{category} 現在庫一覧 <span style="font-size: 11pt; font-weight: normal; margin-left: 20px;">{today_str}</span></h3>
                    {html_table}
                </div>
                """
                st.markdown(print_html, unsafe_allow_html=True)
                
            else:
                display_df['種類'] = display_df['商品'].apply(lambda x: x.split(" ")[0])
                grouped = display_df.groupby('種類')
                
                tables_html = ""
                for base, group_df in grouped:
                    tables_html += f"<div class='group-wrapper'><h4>{base}</h4>"
                    tables_html += "<table><thead><tr><th>商品</th><th>在庫</th><th>確認日</th></tr></thead><tbody>"
                    for _, row in group_df.iterrows():
                        original_row = df[df['name'] == row['商品']].iloc[0]
                        is_alert_row = row['在庫数'] <= original_row['threshold']
                        bg = "background-color: #fee2e2; font-weight: bold;" if is_alert_row else ""
                        last_check = row['最終確認'] if pd.notna(row['最終確認']) else ""
                        tables_html += f"<tr style='{bg}'><td>{row['商品']}</td><td style='text-align: center;'>{row['在庫数']}</td><td>{last_check}</td></tr>"
                    tables_html += "</tbody></table></div>"
                
                print_html = f"""
                <div id="print-area" class="print-uniform">
                    <h3>{category} 現在庫一覧 <span style="font-size: 10pt; font-weight: normal; margin-left: 20px;">{today_str}</span></h3>
                    <div class="masonry-layout">
                        {tables_html}
                    </div>
                </div>
                """
                st.markdown(print_html, unsafe_allow_html=True)
            
        else:
            st.table(display_df.style.hide(axis="index").apply(highlight_alert, axis=1))
        
        if is_alert and not alerts.empty:
            st.markdown("<div class='no-print'>", unsafe_allow_html=True)
            st.markdown("---")
            share_text = "\\n".join([f"「{row['name']}」の在庫が不足しています。" for _, row in alerts.iterrows()])
            btn_html = f"""
            <button class="no-print" onclick="navigator.share({{text: '{share_text}'}}).catch(e=>alert('お使いのブラウザは共有機能に非対応です。表をコピーしてください。'))" 
                style="background: #2563eb; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                LINE等で発注依頼をシェアする
            </button>
            """
            components.html(btn_html, height=60)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("データがありません。")

# ----------------- 履歴ページ -----------------
elif st.session_state.page == "履歴":
    st.markdown("### 履歴")
    res_hist = supabase.table("equip_history").select("*").order("date", desc=True).order("id", desc=True).execute()
    df_hist = pd.DataFrame(res_hist.data)
    
    tab1, tab2 = st.tabs(["制服", "ガラス道具"])
    for tab, cat in zip([tab1, tab2], ["制服", "ガラス道具"]):
        with tab:
            if not df_hist.empty:
                df_cat = get_inventory(cat)
                if not df_cat.empty:
                    df = df_hist[df_hist['item_name'].isin(df_cat['name'].tolist())].copy()
                    
                    if not df.empty:
                        available_years = sorted(list(set([str(d).split("/")[0] for d in df['date'] if pd.notna(d)])), reverse=True)
                        year_options = ["すべて"] + [f"{y}年" for y in available_years]
                        
                        with st.container(border=True):
                            st.markdown("<h5 style='margin-bottom: 15px; color: #475569; font-size: 14px;'>高度な絞り込み検索</h5>", unsafe_allow_html=True)
                            
                            col_s1, col_s2 = st.columns(2)
                            with col_s1:
                                year_s = auto_close_selector("年", year_options, f"hist_year_{cat}")
                            with col_s2:
                                staff_s = auto_close_selector("氏名", ["すべて", "会社購入"] + STAFF_LIST, f"hist_staff_{cat}")
                            
                            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                            item_s = st.text_input("品名で検索 (一部入力でもOK)", key=f"hist_item_{cat}", placeholder="例: ズボン、ジャンパー")
                        
                        if year_s != "すべて":
                            target_year = year_s.replace("年", "")
                            df = df[df['date'].str.startswith(target_year, na=False)]
                        if staff_s != "すべて": 
                            df = df[df['staff_name'] == staff_s]
                        if item_s:
                            df = df[df['item_name'].str.contains(item_s, na=False)]
                        
                        if not df.empty:
                            display_hist = df[['date', 'staff_name', 'item_name', 'action', 'change_amount', 'comment']]
                            display_hist.columns = ['日付', '氏名', '品名', '区分', '数量', '備考']
                            st.table(display_hist.style.hide(axis="index"))
                        else:
                            st.info("条件に一致する履歴がありません。")
                    else:
                        st.info(f"{cat}の履歴がありません。")
            else:
                st.info("履歴がありません。")

# ----------------- 管理ページ -----------------
elif st.session_state.page == "管理":
    st.markdown("### 管理")
    tab_master, tab_staff, tab_fix = st.tabs(["アイテムの編集", "スタッフ管理", "履歴の取消"])
    
    with tab_master:
        col_add, col_edit = st.columns(2)
        
        with col_add:
            with st.container(border=True):
                st.markdown("##### 新規アイテムの追加")
                n_name = st.text_input("品名", key="new_item_name")
                n_cat = st.selectbox("カテゴリ", ["制服", "ガラス道具"], key="new_item_cat")
                n_stock = st.number_input("現在庫", value=0, step=1, key="new_item_stock")
                n_thresh = st.number_input("アラート基準", value=2 if n_cat=="制服" else 4, step=1, key="new_item_thresh")
                
                st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                if st.button("追加する", type="primary", key="btn_add_item"):
                    if n_name:
                        supabase.table("equip_items").insert({"name": n_name, "stock": n_stock, "category": n_cat, "threshold": n_thresh, "last_checked": ""}).execute()
                        st.success("追加しました。")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("品名を入力してください。")

        with col_edit:
            with st.container(border=True):
                st.markdown("##### 既存アイテムの編集・削除")
                edit_cat = st.radio("カテゴリ選択", ["制服", "ガラス道具"], key="edit_cat", horizontal=True)
                df_edit = get_inventory(edit_cat)
                if not df_edit.empty:
                    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
                    edit_item = auto_close_selector("編集するアイテム", df_edit['name'].tolist(), "edit_item_select")
                    row = df_edit[df_edit['name'] == edit_item].iloc[0]
                    
                    e_stock = st.number_input("現在庫を修正", value=int(row['stock']), step=1, key="edit_item_stock")
                    e_thresh = st.number_input("アラート基準を修正", value=int(row['threshold']), step=1, key="edit_item_thresh")
                    
                    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("更新する", type="primary", key="btn_update_item", use_container_width=True):
                            supabase.table("equip_items").update({"stock": e_stock, "threshold": e_thresh}).eq("name", edit_item).execute()
                            st.success("更新しました。")
                            time.sleep(1)
                            st.rerun()
                    with col2:
                        if st.button("削除", key="btn_delete_item", use_container_width=True):
                            supabase.table("equip_items").delete().eq("name", edit_item).execute()
                            st.error("削除しました。")
                            time.sleep(1)
                            st.rerun()

    with tab_staff:
        col_s_add, col_s_edit = st.columns(2)
        with col_s_add:
            with st.container(border=True):
                st.markdown("##### スタッフの追加")
                new_staff = st.text_input("追加するスタッフ名", key="new_staff_name")
                st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                if st.button("スタッフを追加", type="primary", key="btn_add_staff"):
                    if new_staff:
                        supabase.table("equip_items").insert({"name": new_staff, "category": "スタッフ", "stock": 0, "threshold": 0, "last_checked": ""}).execute()
                        st.success("追加しました。")
                        time.sleep(1)
                        st.rerun()

        with col_s_edit:
            with st.container(border=True):
                st.markdown("##### スタッフの削除")
                del_staff = auto_close_selector("削除するスタッフ", STAFF_LIST, "del_staff_select")
                st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                if st.button("削除する", key="btn_delete_staff", use_container_width=True):
                    supabase.table("equip_items").delete().eq("name", del_staff).eq("category", "スタッフ").execute()
                    st.error("削除しました。")
                    time.sleep(1)
                    st.rerun()
                            
    with tab_fix:
        with st.container(border=True):
            st.info("誤って入力してしまった履歴を削除し、在庫数を元に戻します。")
            res_hist = supabase.table("equip_history").select("*").order("id", desc=True).limit(50).execute()
            df_hist = pd.DataFrame(res_hist.data)
            
            if not df_hist.empty:
                options = []
                for _, row in df_hist.iterrows():
                    opt = f"[ID:{row['id']}] {row['date']} | {row['staff_name']} | {row['item_name']} | {row['action']} {row['change_amount']}個"
                    options.append(opt)
                    
                st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
                selected_record = auto_close_selector("削除する履歴 (直近50件)", options, "del_hist_select", horizontal=False)
                    
                record_id = int(selected_record.split("]")[0].replace("[ID:", ""))
                target_row = df_hist[df_hist['id'] == record_id].iloc[0]
                
                st.warning(f"以下の履歴を削除し、在庫数を再計算します。\n\n**{target_row['item_name']}** ({target_row['action']} {target_row['change_amount']}個)")
                
                confirm = st.checkbox("確認しました（この履歴を完全に削除します）", key="confirm_del_hist")
                if confirm:
                    if st.button("履歴を削除して在庫を戻す", type="primary", key="btn_execute_del_hist", use_container_width=True):
                        delete_history_record(record_id, target_row['item_name'], target_row['action'], target_row['change_amount'])
                        st.toast("履歴を削除し、在庫を修正しました。")
                        time.sleep(1.5)
                        st.rerun()
