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
st.set_page_config(page_title="在庫・貸出管理Pro", page_icon="🏢", layout="centered", initial_sidebar_state="expanded")

pro_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body { font-family: 'Inter', sans-serif !important; background-color: #f8fafc; color: #1e293b; }

/* ラジオボタンを洗練されたタブ風/ボタン風に */
div[data-testid="stRadio"] > div[role="radiogroup"] { display: flex; flex-wrap: wrap; gap: 8px; background: #e2e8f0; padding: 6px; border-radius: 12px; margin-bottom: 24px; }
div[data-testid="stRadio"] label { background-color: transparent; padding: 10px 16px !important; border-radius: 8px; cursor: pointer; transition: all 0.2s; border: none; }
div[data-testid="stRadio"] label[data-checked="true"] { background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); color: #0f172a; font-weight: 700; }

/* カード・表のデザイン */
.card-box { background: #ffffff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; margin-bottom: 16px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0;}
th { background-color: #f8fafc; padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0; color: #64748b;}
td { padding: 12px; border-bottom: 1px solid #e2e8f0; }
tr:hover { background-color: #f1f5f9; }

/* 🌟 A4印刷用の完璧なレイアウトCSS (不要なタイトルやチェックボックスを全消去) */
@media print { 
    @page { size: A4 portrait; margin: 10mm; } 
    /* 余計なものを根こそぎ非表示にする */
    .no-print, 
    section[data-testid="stSidebar"], 
    header[data-testid="stHeader"], 
    div[data-testid="stRadio"], 
    div[data-testid="stCheckbox"], 
    button { display: none !important; } 
    
    html, body, .main, .block-container { background: #fff !important; padding: 0 !important; margin: 0 !important; width: 100% !important; max-width: 100% !important; } 
    
    #print-area { width: 100%; color: #000; }
    #print-area table { border: 1px solid #334155; width: 100%; border-collapse: collapse; } 
    #print-area th { background-color: #f1f5f9 !important; font-weight: bold; border: 1px solid #334155 !important; -webkit-print-color-adjust: exact; color: #000; }
    #print-area td { border: 1px solid #334155 !important; }
    
    /* ガラス道具用（1列・文字拡大） */
    .print-glass table { font-size: 14pt; margin-top: 10px; }
    .print-glass th, .print-glass td { padding: 12px; }
    
    /* 制服等用（種類分け・2列レイアウト） */
    .print-uniform { font-size: 10pt; }
    .masonry-layout { column-count: 2; column-gap: 20px; margin-top: 10px; }
    .group-wrapper { break-inside: avoid; page-break-inside: avoid; margin-bottom: 15px; }
    .print-uniform th, .print-uniform td { padding: 4px 6px; }
}
</style>
"""
st.markdown(pro_css, unsafe_allow_html=True)

# ==========================================
# 4. ナビゲーション・タイトル
# ==========================================
PAGES = ["📝 入力", "📦 在庫一覧", "📚 履歴", "⚙️ 管理"]
if "page" not in st.session_state: 
    st.session_state.page = "📝 入力"

st.sidebar.markdown("<h2 style='text-align: center; color: #1e293b; margin-bottom: 30px;'>🏢 管理メニュー</h2>", unsafe_allow_html=True)
for p in PAGES:
    if st.sidebar.button(p, use_container_width=True, type="primary" if st.session_state.page == p else "secondary"):
        st.session_state.page = p
        st.rerun()

# 印刷時に消えるように .no-print クラスで囲む
st.markdown("<div class='no-print'><h3 style='color: #1e293b; margin-top: -20px; margin-bottom: 10px; font-weight: 700;'>🏢 備品・制服 貸出管理</h3></div>", unsafe_allow_html=True)
st.radio("メニュー", PAGES, horizontal=True, label_visibility="collapsed", key="page")

# ==========================================
# 5. 各画面ロジック
# ==========================================

# ----------------- 📝 入力ページ -----------------
if st.session_state.page == "📝 入力":
    tab1, tab2 = st.tabs(["👕 制服", "🪟 ガラス道具"])
    
    with tab1:
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        action_u = st.radio("区分", ["支給", "補充"], horizontal=True, key="action_u")
        
        if action_u == "補充":
            st.text_input("👤 補充元", value="会社購入", disabled=True, key="staff_add_u")
            staff_u = "会社購入"
        else:
            with st.expander("👤 支給するスタッフを選択"):
                staff_u = st.radio("スタッフ名", STAFF_LIST, label_visibility="collapsed", key="staff_give_u")
        
        df_u = get_inventory("制服")
        if not df_u.empty:
            base_types = sorted(list(set([name.split(" ")[0] for name in df_u['name'].tolist()])))
            with st.expander("👔 種類を選択"):
                selected_base = st.radio("種類", base_types, label_visibility="collapsed", key="base_u")
                
            size_options = [n for n in df_u['name'].tolist() if n.startswith(selected_base)]
            item_u = st.radio("サイズ", size_options, horizontal=True, key="item_u")
        else:
            with st.expander("👔 品名を選択"):
                item_u = st.radio("品名", ["データなし"], label_visibility="collapsed", key="item_u_empty")
            
        qty_u = st.number_input("数量", min_value=1, value=1, step=1, key="qty_u")
        comment_u = st.text_input("備考", key="comment_u")
        
        if st.button("記録する", type="primary", use_container_width=True, key="btn_u"):
            process_action(staff_u, action_u, item_u, qty_u, comment_u)
            st.success("完了しました！")
            time.sleep(0.5)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        action_g = st.radio("区分", ["支給", "補充"], horizontal=True, key="action_g")
        
        if action_g == "補充":
            st.text_input("👤 補充元", value="会社購入", disabled=True, key="staff_add_g")
            staff_g = "会社購入"
        else:
            with st.expander("👤 支給するスタッフを選択"):
                staff_g = st.radio("スタッフ名", STAFF_LIST, label_visibility="collapsed", key="staff_give_g")
        
        df_g = get_inventory("ガラス道具")
        item_list_g = df_g['name'].tolist() if not df_g.empty else []
        with st.expander("🪟 品名を選択"):
            item_g = st.radio("品名", item_list_g, label_visibility="collapsed", key="item_g")
        
        qty_g = st.number_input("数量", min_value=1, value=1, step=1, key="qty_g")
        comment_g = st.text_input("備考", key="comment_g")
        
        if st.button("記録する", type="primary", use_container_width=True, key="btn_g"):
            process_action(staff_g, action_g, item_g, qty_g, comment_g)
            st.success("完了しました！")
            time.sleep(0.5)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------- 📦 在庫一覧ページ -----------------
elif st.session_state.page == "📦 在庫一覧":
    category = st.radio("カテゴリ", ["制服", "ガラス道具"], horizontal=True, key="inv_cat")
    df = get_inventory(category)
    
    if not df.empty:
        alerts = df[df['stock'] <= df['threshold']]
        
        col1, col2 = st.columns(2)
        with col1: 
            is_alert = st.checkbox("🚨 不足分のみ表示", key="inv_alert")
        with col2: 
            print_mode = st.checkbox("🖨️ A4印刷モード", key="inv_print")
        
        display_df = (alerts if is_alert else df)[['name', 'stock', 'last_checked']]
        display_df.columns = ['商品', '在庫数', '最終確認']
        
        def highlight_alert(row):
            original_row = df[df['name'] == row['商品']].iloc[0]
            if row['在庫数'] <= original_row['threshold']:
                return ['background-color: #fee2e2; color: #991b1b; font-weight: bold;'] * len(row)
            return [''] * len(row)
        
        if print_mode:
            st.markdown("<div class='no-print' style='background: #d1e7dd; padding: 15px; border-radius: 8px; color: #0f5132; margin-bottom: 20px;'>Ctrl+P (スマホの場合は共有ボタン) から印刷を実行してください。<br>※上部のタイトル等は印刷時に自動で消去されます。</div>", unsafe_allow_html=True)
            
            # 印刷日時の取得
            today_str = datetime.now().strftime("%Y年%m月%d日")
            
            if category == "ガラス道具":
                # ガラス道具: 1列で文字を拡大
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
                    <h3 style="margin-bottom: 10px; font-size: 16pt; border-bottom: 2px solid #334155; padding-bottom: 5px;">
                        {category} 現在庫一覧 <span style="font-size: 12pt; font-weight: normal; margin-left: 20px;">{today_str}</span>
                    </h3>
                    {html_table}
                </div>
                """
                st.markdown(print_html, unsafe_allow_html=True)
                
            else:
                # 制服: 種類ごとに分けて2列で表示
                display_df['種類'] = display_df['商品'].apply(lambda x: x.split(" ")[0])
                grouped = display_df.groupby('種類')
                
                tables_html = ""
                for base, group_df in grouped:
                    tables_html += f"<div class='group-wrapper'><h4 style='margin: 0 0 5px 0; padding-bottom: 3px; border-bottom: 2px solid #334155; color: #1e293b;'>{base}</h4>"
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
                    <h3 style="margin-bottom: 10px; font-size: 16pt; border-bottom: 2px solid #334155; padding-bottom: 5px;">
                        {category} 現在庫一覧 <span style="font-size: 12pt; font-weight: normal; margin-left: 20px;">{today_str}</span>
                    </h3>
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
                style="background: #06C755; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%;">
                💬 LINE等で発注依頼をシェアする
            </button>
            """
            components.html(btn_html, height=60)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("データがありません。")

# ----------------- 📚 履歴ページ -----------------
elif st.session_state.page == "📚 履歴":
    st.markdown("### 📚 履歴")
    res_hist = supabase.table("equip_history").select("*").order("date", desc=True).order("id", desc=True).execute()
    df_hist = pd.DataFrame(res_hist.data)
    
    tab1, tab2 = st.tabs(["👕 制服", "🪟 ガラス道具"])
    for tab, cat in zip([tab1, tab2], ["制服", "ガラス道具"]):
        with tab:
            if not df_hist.empty:
                df_cat = get_inventory(cat)
                if not df_cat.empty:
                    df = df_hist[df_hist['item_name'].isin(df_cat['name'].tolist())]
                    
                    with st.expander(f"👤 氏名で絞り込み ({cat})"):
                        staff_s = st.radio(f"氏名 ({cat})", ["すべて", "会社購入"] + STAFF_LIST, label_visibility="collapsed", key=f"hist_staff_{cat}")
                        
                    if staff_s != "すべて": 
                        df = df[df['staff_name'] == staff_s]
                    
                    if not df.empty:
                        display_hist = df[['date', 'staff_name', 'item_name', 'action', 'change_amount', 'comment']]
                        display_hist.columns = ['日付', '氏名', '品名', '区分', '数量', '備考']
                        st.table(display_hist.style.hide(axis="index"))
                    else:
                        st.info("該当する履歴がありません。")
            else:
                st.info("履歴がありません。")

# ----------------- ⚙️ 管理ページ -----------------
elif st.session_state.page == "⚙️ 管理":
    st.markdown("### ⚙️ 管理")
    tab_master, tab_staff, tab_fix = st.tabs(["📝 アイテムの編集", "👤 スタッフ管理", "🗑️ 履歴の取消"])
    
    with tab_master:
        st.info("💡 アイテムの追加、および既存のアイテムの「在庫数」「アラート基準」を変更・削除できます。")
        col_add, col_edit = st.columns(2)
        
        with col_add:
            st.markdown("<div class='card-box'>", unsafe_allow_html=True)
            st.markdown("##### ▶ 新規アイテムの追加")
            n_name = st.text_input("品名", key="new_item_name")
            n_cat = st.radio("カテゴリ", ["制服", "ガラス道具"], horizontal=True, key="new_item_cat")
            n_stock = st.number_input("現在庫", value=0, step=1, key="new_item_stock")
            n_thresh = st.number_input("アラート基準", value=2 if n_cat=="制服" else 4, step=1, key="new_item_thresh")
            if st.button("追加する", type="primary", key="btn_add_item"):
                if n_name:
                    supabase.table("equip_items").insert({"name": n_name, "stock": n_stock, "category": n_cat, "threshold": n_thresh, "last_checked": ""}).execute()
                    st.success(f"{n_name} を追加しました！")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("品名を入力してください。")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_edit:
            st.markdown("<div class='card-box'>", unsafe_allow_html=True)
            st.markdown("##### ▶ 既存アイテムの編集・削除")
            edit_cat = st.radio("カテゴリ選択", ["制服", "ガラス道具"], key="edit_cat", horizontal=True)
            df_edit = get_inventory(edit_cat)
            if not df_edit.empty:
                with st.expander("✏️ 編集するアイテムを選択"):
                    edit_item = st.radio("アイテム", df_edit['name'].tolist(), label_visibility="collapsed", key="edit_item_select")
                
                row = df_edit[df_edit['name'] == edit_item].iloc[0]
                
                e_stock = st.number_input("現在庫を修正", value=int(row['stock']), step=1, key="edit_item_stock")
                e_thresh = st.number_input("アラート基準を修正", value=int(row['threshold']), step=1, key="edit_item_thresh")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("更新する", type="primary", key="btn_update_item"):
                        supabase.table("equip_items").update({"stock": e_stock, "threshold": e_thresh}).eq("name", edit_item).execute()
                        st.success("更新しました！")
                        time.sleep(1)
                        st.rerun()
                with col2:
                    if st.button("🚨 削除", key="btn_delete_item"):
                        supabase.table("equip_items").delete().eq("name", edit_item).execute()
                        st.error("削除しました。")
                        time.sleep(1)
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_staff:
        st.info("💡 アプリで選択できるスタッフの名前を追加・削除できます。")
        col_s_add, col_s_edit = st.columns(2)
        with col_s_add:
            st.markdown("<div class='card-box'>", unsafe_allow_html=True)
            st.markdown("##### ▶ スタッフの追加")
            new_staff = st.text_input("追加するスタッフ名", key="new_staff_name")
            if st.button("スタッフを追加", type="primary", key="btn_add_staff"):
                if new_staff:
                    supabase.table("equip_items").insert({"name": new_staff, "category": "スタッフ", "stock": 0, "threshold": 0, "last_checked": ""}).execute()
                    st.success(f"{new_staff} を追加しました！")
                    time.sleep(1)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with col_s_edit:
            st.markdown("<div class='card-box'>", unsafe_allow_html=True)
            st.markdown("##### ▶ スタッフの削除")
            with st.expander("🚨 削除するスタッフを選択"):
                del_staff = st.radio("スタッフ", STAFF_LIST, label_visibility="collapsed", key="del_staff_select")
                
            if st.button("🚨 削除する", key="btn_delete_staff"):
                supabase.table("equip_items").delete().eq("name", del_staff).eq("category", "スタッフ").execute()
                st.error(f"{del_staff} を削除しました。")
                time.sleep(1)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
                            
    with tab_fix:
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        st.info("誤って入力してしまった履歴を安全に削除し、在庫数を元に戻します。")
        res_hist = supabase.table("equip_history").select("*").order("id", desc=True).limit(50).execute()
        df_hist = pd.DataFrame(res_hist.data)
        
        if not df_hist.empty:
            options = []
            for _, row in df_hist.iterrows():
                opt = f"[ID:{row['id']}] {row['date']} | {row['staff_name']} | {row['item_name']} | {row['action']} {row['change_amount']}個"
                options.append(opt)
                
            with st.expander("🗑️ 削除する履歴を選択 (直近50件)"):
                selected_record = st.radio("履歴", options, label_visibility="collapsed", key="del_hist_select")
                
            record_id = int(selected_record.split("]")[0].replace("[ID:", ""))
            target_row = df_hist[df_hist['id'] == record_id].iloc[0]
            
            st.warning(f"以下の履歴を削除し、在庫数を再計算します。\n\n**{target_row['item_name']}** ({target_row['action']} {target_row['change_amount']}個)")
            
            confirm = st.checkbox("⚠️ 確認しました（この履歴を完全に削除します）", key="confirm_del_hist")
            if confirm:
                if st.button("🚨 履歴を削除して在庫を戻す", type="primary", key="btn_execute_del_hist"):
                    delete_history_record(record_id, target_row['item_name'], target_row['action'], target_row['change_amount'])
                    st.toast("履歴を削除し、在庫を修正しました。", icon="🗑️")
                    time.sleep(1.5)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
