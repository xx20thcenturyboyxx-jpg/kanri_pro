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
# 3. モダンUI・CSS設定
# ==========================================
st.set_page_config(page_title="在庫・貸出管理Pro", page_icon="🏢", layout="centered", initial_sidebar_state="collapsed")

pro_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif !important; color: #1e293b; background-color: #f8fafc; }
div[data-testid="stRadio"] > div { display: flex; flex-wrap: wrap; gap: 10px; background: #ffffff; padding: 10px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px;}
div[data-testid="stRadio"] label { background-color: #f1f5f9; padding: 10px 15px !important; border-radius: 8px; cursor: pointer; transition: all 0.2s; border: 1px solid transparent; }
div[data-testid="stRadio"] label[data-checked="true"] { background-color: #e0f2fe; border-color: #3b82f6; color: #1d4ed8; font-weight: bold; }
table { width: 100%; border-collapse: collapse; background-color: #ffffff; margin-bottom: 20px; font-size: 14px; }
th { background-color: #f8fafc; border-bottom: 2px solid #e2e8f0; padding: 12px 15px; text-align: left; color: #475569; font-weight: 700; }
td { border-bottom: 1px solid #e2e8f0; padding: 12px 15px; color: #334155; }
.card-box { background-color: #ffffff; border-radius: 16px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; margin-bottom: 20px;}
</style>
"""
st.markdown(pro_css, unsafe_allow_html=True)

# ==========================================
# 4. ヘッダー・横並びナビゲーション
# ==========================================
st.markdown("<h2 style='text-align: center; color: #1e293b; margin-top: -30px; margin-bottom: 20px;'>🏢 在庫・貸出管理</h2>", unsafe_allow_html=True)

PAGES = ["📝 入力", "📦 在庫一覧", "👤 個別履歴", "📚 全履歴", "⚙️ 管理"]
selected_page = st.radio("メニュー", PAGES, horizontal=True, label_visibility="collapsed")

# ==========================================
# 5. 各画面のロジック
# ==========================================
if selected_page == "📝 入力":
    tab1, tab2 = st.tabs(["👕 制服", "🪟 ガラス道具"])
    
    # --- 制服の入力フォーム（2段階ドロップダウン対応） ---
    with tab1:
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #1e293b; margin-bottom: 20px;'>👕 制服の入力フォーム</h4>", unsafe_allow_html=True)
        
        # 動的UIのため st.form を使用しない
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
            # 「冬シャツ」「ズボン」などの種類だけを抽出
            base_types = sorted(list(set([name.split(" ")[0] for name in all_u_names])))
            
            with col_u2:
                selected_base = st.selectbox("種類を選択", base_types, key="base_u")
            
            # 選んだ種類に合致するサイズだけを抽出
            size_options = [name for name in all_u_names if name.startswith(selected_base)]
            item_u = st.selectbox("サイズを選択", size_options, key="item_u")
        else:
            item_u = st.selectbox("品名を選択", ["データなし"], key="item_u_empty")

        qty_u = st.number_input("数量", min_value=1, value=1, step=1, key="qty_u")
        comment_u = st.text_input("備考 (任意)", placeholder="例: サイズ交換、破損など", key="comment_u")
        
        if st.button("記録する (制服)", type="primary", use_container_width=True, key="btn_u"):
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
        st.markdown("<h4 style='color: #1e293b; margin-bottom: 20px;'>🪟 ガラス道具の入力フォーム</h4>", unsafe_allow_html=True)
        
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
        
        if st.button("記録する (ガラス道具)", type="primary", use_container_width=True, key="btn_g"):
            if action_g == "支給" and not staff_g.strip():
                st.error("⚠️ スタッフ名を入力してください。")
            else:
                process_action(staff_g, action_g, item_g, qty_g, comment_g)
                st.success(f"✅ {item_g} を{qty_g}個 {action_g}として記録しました！")
                time.sleep(1)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif selected_page == "📦 在庫一覧":
    category = st.radio("表示カテゴリ", ["制服", "ガラス道具"], horizontal=True)
    df = get_inventory(category)
    
    if not df.empty:
        alerts = df[df['stock'] <= df['threshold']]
        is_alert_mode = st.checkbox(f"🚨 発注が必要なアイテムのみ表示 ({len(alerts)}件)", value=False)
        display_df = alerts if is_alert_mode else df
        
        # 画像のフォーマットに合わせた列作成
        display_df = display_df[['name', 'stock', 'category', 'last_checked', 'threshold']].copy()
        display_df['備考'] = ""
        display_df.columns = ['商品', '在庫数', '分類', '最終確認', 'アラート基準', '備考']
        
        # 表示用データフレーム（アラート基準は隠す）
        table_df = display_df[['商品', '在庫数', '分類', '最終確認', '備考']]
        
        def highlight_alert(row):
            # 現在庫が基準以下なら薄い赤色に
            if row['在庫数'] <= display_df.loc[row.name, 'アラート基準']:
                return ['background-color: #fee2e2'] * len(row)
            return [''] * len(row)

        st.markdown("<div style='margin-top: 10px;'>", unsafe_allow_html=True)
        # st.table と .hide(axis="index") で画像通りの綺麗な一覧表を表示（スクロールなしで全件表示）
        st.table(table_df.style.hide(axis="index").apply(highlight_alert, axis=1))
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("データがありません。")

elif selected_page == "👤 個別履歴":
    st.markdown("### 👤 スタッフ別 支給履歴リスト")
    st.info("スタッフごとに「いつ・何を・いくつ」支給したかを時系列で確認できます。")
    
    res_hist = supabase.table("equip_history").select("*").eq("action", "支給").order("date", desc=True).order("id", desc=True).execute()
    df_hist = pd.DataFrame(res_hist.data)
    
    if not df_hist.empty:
        # 存在するスタッフ名のリストを取得
        staff_list = sorted(list(set(df_hist['staff_name'].tolist())))
        selected_staff = st.selectbox("検索するスタッフを選択してください", ["-- 選択してください --"] + staff_list)
        
        if selected_staff != "-- 選択してください --":
            staff_df = df_hist[df_hist['staff_name'] == selected_staff].copy()
            staff_df = staff_df[['date', 'item_name', 'change_amount', 'comment']]
            staff_df.columns = ['支給日', '支給アイテム', '数量', '備考']
            
            st.markdown(f"**{selected_staff}** さんの支給履歴（計 {len(staff_df)} 件）")
            st.table(staff_df.style.hide(axis="index"))
    else:
        st.warning("支給履歴がまだありません。")

elif selected_page == "📚 全履歴":
    st.markdown("### 📚 すべての出入り履歴")
    res_hist = supabase.table("equip_history").select("*").order("date", desc=True).order("id", desc=True).execute()
    df_hist = pd.DataFrame(res_hist.data)
    
    if not df_hist.empty:
        search_word = st.text_input("🔍 スタッフ名・品名で絞り込み")
        if search_word:
            df_hist = df_hist[df_hist['staff_name'].str.contains(search_word, na=False) | df_hist['item_name'].str.contains(search_word, na=False)]
            
        display_hist = df_hist[['date', 'staff_name', 'item_name', 'action', 'change_amount', 'comment']]
        display_hist.columns = ['日付', '氏名', '品名', '区分', '数量', '備考']
        
        st.dataframe(display_hist, use_container_width=True, hide_index=True)
    else:
        st.info("履歴がありません。")

elif selected_page == "⚙️ 管理":
    st.markdown("### ⚙️ 管理・修正機能")
    tab_master, tab_fix = st.tabs(["📝 アイテムの編集・追加", "🗑️ 履歴の削除(取消)"])
    
    with tab_master:
        st.info("💡 アイテムの追加、および既存のアイテムの「在庫数」「アラート基準」を変更・削除できます。")
        col_add, col_edit = st.columns(2)
        
        with col_add:
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

        with col_edit:
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
