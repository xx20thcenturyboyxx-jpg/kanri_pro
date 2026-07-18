import streamlit as st
import pandas as pd
from datetime import datetime
import time
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
    date_str = datetime.now().strftime("%Y/%m/%d")
    stock_diff = qty if action == "追加" else -qty
        
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
# 3. 超モダンUI・CSS設定 (プロ仕様)
# ==========================================
st.set_page_config(page_title="在庫・貸出管理Pro", page_icon="🏢", layout="centered", initial_sidebar_state="expanded")

pro_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', 'Noto Sans JP', sans-serif !important; color: #1e293b; background-color: #f8fafc; }

/* 上部ラジオボタンを洗練されたタブ風に */
div[data-testid="stRadio"] > div[role="radiogroup"] { display: flex; flex-wrap: wrap; gap: 8px; background: #e2e8f0; padding: 6px; border-radius: 12px; margin-bottom: 24px; }
div[data-testid="stRadio"] label { background-color: transparent; padding: 10px 16px !important; border-radius: 8px; cursor: pointer; transition: all 0.2s; border: none; }
div[data-testid="stRadio"] label[data-checked="true"] { background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); color: #0f172a; font-weight: 700; }

/* フォーム・カード領域の浮き出し効果 */
.card-box { background-color: #ffffff; border-radius: 16px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03); border: 1px solid #e2e8f0; margin-bottom: 24px; }

/* 入力フィールドのプロフェッショナル化 */
input, div[data-baseweb="select"] > div { background-color: #f8fafc !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; color: #334155 !important; transition: all 0.2s ease; }
input:focus, div[data-baseweb="select"] > div:focus-within { border-color: #3b82f6 !important; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important; background-color: #ffffff !important;}

/* 数量入力の視認性向上 */
div[data-testid="stNumberInput"] input { font-size: 1.25rem !important; font-weight: 700 !important; text-align: center;}

/* プライマリーボタンのリッチ化 */
button[data-testid="baseButton-primary"] { background: #2563eb !important; border: none !important; border-radius: 8px !important; box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2) !important; padding: 0.5rem 1rem !important; transition: all 0.2s ease !important; }
button[data-testid="baseButton-primary"]:hover { background: #1d4ed8 !important; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.3) !important; transform: translateY(-1px); }
button[data-testid="baseButton-primary"] p { color: #ffffff !important; font-weight: 600 !important; font-size: 1rem !important; }

/* テーブル（表）のエンタープライズ仕様 */
table { width: 100%; border-collapse: collapse; background-color: #ffffff; margin-bottom: 20px; font-size: 14px; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0;}
th { background-color: #f8fafc; border-bottom: 2px solid #e2e8f0; padding: 12px 16px; text-align: left; color: #64748b; font-weight: 700; font-size: 13px; }
td { border-bottom: 1px solid #e2e8f0; padding: 12px 16px; color: #334155; }
tr:hover { background-color: #f1f5f9; }
</style>
"""
st.markdown(pro_css, unsafe_allow_html=True)

# ==========================================
# 4. ヘッダー・ナビゲーション (サイド & 上部 連動)
# ==========================================
PAGES = ["📝 入力", "📦 在庫一覧", "👤 個別履歴", "📚 全履歴", "⚙️ 管理"]

if "page" not in st.session_state:
    st.session_state.page = "📝 入力"

# --- サイドバー ---
st.sidebar.markdown("<h2 style='text-align: center; color: #1e293b; margin-bottom: 30px;'>🏢 管理メニュー</h2>", unsafe_allow_html=True)
for p in PAGES:
    if st.sidebar.button(p, use_container_width=True, type="primary" if st.session_state.page == p else "secondary"):
        st.session_state.page = p
        st.rerun()
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 Inventory Pro")

# --- 上部メニュー ---
st.markdown("<h3 style='color: #1e293b; margin-top: -20px; margin-bottom: 10px; font-weight: 700;'>🏢 備品・制服 貸出管理</h3>", unsafe_allow_html=True)
st.radio("メニュー", PAGES, horizontal=True, label_visibility="collapsed", key="page")


# ==========================================
# 5. 各画面のロジック
# ==========================================
if st.session_state.page == "📝 入力":
    tab1, tab2 = st.tabs(["👕 制服", "🪟 ガラス道具"])
    
    # --- 制服の入力フォーム（2段階ドロップダウン対応） ---
    with tab1:
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #1e293b; margin-bottom: 20px; font-weight: 700;'>👕 制服の出入り記録</h4>", unsafe_allow_html=True)
        
        action_u = st.radio("区分", ["支給", "追加"], horizontal=True, key="action_u")
        
        col_u1, col_u2 = st.columns([1, 1])
        with col_u1:
            if action_u == "追加":
                staff_u = st.text_input("👤 スタッフ名", value="会社購入", disabled=True, key="staff_u_add")
            else:
                staff_u = st.text_input("👤 スタッフ名 (必須)", value="青山", key="staff_u_give")
        
        # 2段階ドロップダウンのロジック
        df_u = get_inventory("制服")
        if not df_u.empty:
            all_u_names = df_u['name'].tolist()
            base_types = sorted(list(set([name.split(" ")[0] for name in all_u_names])))
            
            with col_u2:
                selected_base = st.selectbox("種類を選択", base_types, key="base_u")
            
            size_options = [name for name in all_u_names if name.startswith(selected_base)]
            item_u = st.selectbox("サイズを選択", size_options, key="item_u")
        else:
            item_u = st.selectbox("品名を選択", ["データなし"], key="item_u_empty")

        qty_u = st.number_input("数量", min_value=1, value=1, step=1, key="qty_u")
        comment_u = st.text_input("備考 (任意)", placeholder="例: サイズ交換、破損など", key="comment_u")
        
        if st.button("この内容で記録する", type="primary", use_container_width=True, key="btn_u"):
            if action_u == "支給" and not staff_u.strip():
                st.error("⚠️ スタッフ名を入力してください。")
            else:
                process_action(staff_u, action_u, item_u, qty_u, comment_u)
                st.success(f"✅ {item_u} を{qty_u}個 {action_u}として記録しました！")
                time.sleep(1)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- ガラス道具の入力フォーム ---
    with tab2:
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #1e293b; margin-bottom: 20px; font-weight: 700;'>🪟 ガラス道具の出入り記録</h4>", unsafe_allow_html=True)
        
        action_g = st.radio("区分", ["支給", "追加"], horizontal=True, key="action_g")
        
        col_g1, col_g2 = st.columns([1, 1])
        with col_g1:
            if action_g == "追加":
                staff_g = st.text_input("👤 スタッフ名", value="会社購入", disabled=True, key="staff_g_add")
            else:
                staff_g = st.text_input("👤 スタッフ名 (必須)", value="青山", key="staff_g_give")
        
        df_g = get_inventory("ガラス道具")
        item_list_g = df_g['name'].tolist() if not df_g.empty else []
        with col_g2:
            item_g = st.selectbox("品名を選択", item_list_g, key="item_g")
            
        qty_g = st.number_input("数量", min_value=1, value=1, step=1, key="qty_g")
        comment_g = st.text_input("備考 (任意)", key="comment_g")
        
        if st.button("この内容で記録する", type="primary", use_container_width=True, key="btn_g"):
            if action_g == "支給" and not staff_g.strip():
                st.error("⚠️ スタッフ名を入力してください。")
            else:
                process_action(staff_g, action_g, item_g, qty_g, comment_g)
                st.success(f"✅ {item_g} を{qty_g}個 {action_g}として記録しました！")
                time.sleep(1)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "📦 在庫一覧":
    category = st.radio("表示カテゴリ", ["制服", "ガラス道具"], horizontal=True)
    df = get_inventory(category)
    
    if not df.empty:
        alerts = df[df['stock'] <= df['threshold']]
        is_alert_mode = st.checkbox(f"🚨 発注が必要なアイテムのみ表示 ({len(alerts)}件)", value=False)
        display_df = alerts if is_alert_mode else df
        
        # 必要な列を整理し、表示用の設定を行う
        display_df = display_df[['name', 'stock', 'category', 'last_checked', 'threshold']].copy()
        display_df['備考'] = ""
        display_df.columns = ['商品', '在庫数', '分類', '最終確認', 'アラート基準', '備考']
        
        def highlight_alert(row):
            # 現在庫が基準以下なら、背景を薄赤・文字を濃い赤・太字にする
            if row['在庫数'] <= row['アラート基準']:
                return ['background-color: #fee2e2; color: #991b1b; font-weight: 700;'] * len(row)
            return [''] * len(row)

        # アラート基準列は判定に使うが表示からは隠す
        styled_table = display_df.style.hide(axis="index").hide(subset=["アラート基準"], axis="columns").apply(highlight_alert, axis=1)

        st.markdown("<div style='margin-top: 15px;'>", unsafe_allow_html=True)
        st.table(styled_table)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("データがありません。")

elif st.session_state.page == "👤 個別履歴":
    st.markdown("### 👤 スタッフ別 支給履歴リスト")
    st.info("スタッフごとに「いつ・何を・いくつ」支給したかを時系列で確認できます。")
    
    res_hist = supabase.table("equip_history").select("*").eq("action", "支給").order("date", desc=True).order("id", desc=True).execute()
    df_hist = pd.DataFrame(res_hist.data)
    
    if not df_hist.empty:
        staff_list = sorted(list(set(df_hist['staff_name'].tolist())))
        selected_staff = st.selectbox("検索するスタッフを選択", ["-- 選択してください --"] + staff_list)
        
        if selected_staff != "-- 選択してください --":
            staff_df = df_hist[df_hist['staff_name'] == selected_staff].copy()
            staff_df = staff_df[['date', 'item_name', 'change_amount', 'comment']]
            staff_df.columns = ['支給日', '支給アイテム', '数量', '備考']
            
            st.markdown(f"<div class='card-box'><h5 style='margin-bottom: 15px;'>{selected_staff} さんの支給履歴（計 {len(staff_df)} 件）</h5>", unsafe_allow_html=True)
            st.table(staff_df.style.hide(axis="index"))
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("支給履歴がまだありません。")

elif st.session_state.page == "📚 全履歴":
    st.markdown("### 📚 すべての出入り履歴")
    res_hist = supabase.table("equip_history").select("*").order("date", desc=True).order("id", desc=True).execute()
    df_hist = pd.DataFrame(res_hist.data)
    
    if not df_hist.empty:
        search_word = st.text_input("🔍 スタッフ名・品名で絞り込み")
        if search_word:
            df_hist = df_hist[df_hist['staff_name'].str.contains(search_word, na=False) | df_hist['item_name'].str.contains(search_word, na=False)]
            
        display_hist = df_hist[['date', 'staff_name', 'item_name', 'action', 'change_amount', 'comment']]
        display_hist.columns = ['日付', '氏名', '品名', '区分', '数量', '備考']
        
        st.table(display_hist.style.hide(axis="index"))
    else:
        st.info("履歴がありません。")

elif st.session_state.page == "⚙️ 管理":
    st.markdown("### ⚙️ 管理・修正機能")
    tab_master, tab_fix = st.tabs(["📝 アイテムの編集・追加", "🗑️ 履歴の削除(取消)"])
    
    with tab_master:
        st.info("💡 アイテムの追加、および既存のアイテムの「在庫数」「アラート基準」を変更・削除できます。")
        col_add, col_edit = st.columns(2)
        
        with col_add:
            st.markdown("<div class='card-box'>", unsafe_allow_html=True)
            st.markdown("##### ▶ 新規アイテムの追加")
            n_name = st.text_input("品名")
            n_cat = st.selectbox("カテゴリ", ["制服", "ガラス道具"])
            n_stock = st.number_input("現在庫", value=0, step=1)
            n_thresh = st.number_input("アラート基準", value=2 if n_cat=="制服" else 4, step=1)
            if st.button("追加する", type="primary"):
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
                edit_item = st.selectbox("編集するアイテムを選択", df_edit['name'].tolist())
                row = df_edit[df_edit['name'] == edit_item].iloc[0]
                
                e_stock = st.number_input("現在庫を修正", value=int(row['stock']), step=1)
                e_thresh = st.number_input("アラート基準を修正", value=int(row['threshold']), step=1)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("更新する", type="primary"):
                        supabase.table("equip_items").update({"stock": e_stock, "threshold": e_thresh}).eq("name", edit_item).execute()
                        st.success("更新しました！")
                        time.sleep(1)
                        st.rerun()
                with col2:
                    if st.button("🚨 削除"):
                        supabase.table("equip_items").delete().eq("name", edit_item).execute()
                        st.error("削除しました。")
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
        st.markdown("</div>", unsafe_allow_html=True)
