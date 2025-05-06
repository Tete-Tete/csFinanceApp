import streamlit as st
import pandas as pd
import os
import re

st.set_page_config(page_title="CS 饰品记账", layout="wide")
st.markdown("""
    <style>
        body {
            background-color: #f2f6fc;
            font-family: "Microsoft YaHei", sans-serif;
        }
        .css-18e3th9 {
            font-family: "Microsoft YaHei", sans-serif;
        }
    </style>
""", unsafe_allow_html=True)

# ---------- 磨损等级判定 ----------
def get_wear_grade(wear_float):
    if pd.isna(wear_float):
        return ""
    if wear_float <= 0.07:
        return "崭新出厂"
    elif wear_float <= 0.15:
        return "略有磨损"
    elif wear_float <= 0.38:
        return "久经沙场"
    elif wear_float <= 0.45:
        return "战痕累累"
    else:
        return "破损不堪"

# ---------- 清洗旧“磨损+中文”混合字段 ----------
def clean_old_wear_column(df):
    wear_values, wear_grades = [], []
    for val in df['磨损']:
        if isinstance(val, str):
            match = re.match(r"([0-9.]+)", val)
            num = float(match.group(1)) if match else None
        elif isinstance(val, (float, int)):
            num = float(val)
        else:
            num = None
        wear_values.append(num)
        wear_grades.append(get_wear_grade(num))
    df['磨损'] = wear_values
    df['磨损等级'] = wear_grades
    return df

# ---------- 字段顺序 ----------
expected_columns = ['购买物品', '购买平台', '磨损', '磨损等级', '购入价格', '购入时间',
                    '卖出价格', '卖出平台', '卖出时间', '实际到手价格', '毛利']

# ---------- 初始化 ----------
if 'data' not in st.session_state:
    if os.path.exists("cs_log.csv"):
        df = pd.read_csv("cs_log.csv")
        df = df.reindex(columns=expected_columns)
        df = clean_old_wear_column(df)
        st.session_state.data = df
    else:
        st.session_state.data = pd.DataFrame(columns=expected_columns)

st.title("🎮 CS 饰品记账 App")

# ---------- 侧边栏计算器 ----------
st.sidebar.header("🧮 计算工具")

exchange_rate = st.sidebar.number_input("当前汇率（¥ / $）", value=7.34233, step=0.0001, format="%.5f")

st.sidebar.markdown("#### 💵 CSFloat → 悠悠/BUFF")
float_price = st.sidebar.number_input("CSFloat 价格", value=0.0, step=0.01)
if float_price > 0:
    total_cost = float_price * 1.028 + 2.18 + 0.005 * exchange_rate
    st.sidebar.success(f"💰 总人民币成本 ≈ ￥{total_cost:.2f}")

st.sidebar.markdown("#### 💴 悠悠/BUFF → CSFloat")
rmb_total = st.sidebar.number_input("悠悠/BUFF总价格", value=0.0, step=0.01)
if rmb_total > 0:
    float_reverse = (rmb_total - 2.18 - 0.005 * exchange_rate) / 1.028
    st.sidebar.success(f"🎯 对应 CSFloat价格 ≈ {float_reverse:.2f}")

st.sidebar.markdown("#### 📈 利润计算器")
market_price = st.sidebar.number_input("市场单价（¥）", value=0.0, step=0.01)
pickup_price = st.sidebar.number_input("提货价（¥）", value=0.0, step=0.01)
quantity = st.sidebar.number_input("数量", min_value=1, value=1, step=1)
if market_price > 0 and pickup_price > 0:
    unit_profit = market_price - pickup_price
    total_profit = unit_profit * quantity
    st.sidebar.info(f"每件利润：￥{unit_profit:.2f}")
    st.sidebar.success(f"总利润：￥{total_profit:.2f}")

st.sidebar.markdown("#### 🧮 普通计算器")
expr = st.sidebar.text_input("输入数学表达式", placeholder="如：120 + 30 * 0.95")
if expr:
    try:
        result = eval(expr)
        st.sidebar.success(f"结果：{result}")
    except Exception as e:
        st.sidebar.error(f"错误：{e}")

# ---------- 上传账本 ----------
st.subheader("📂 上传 CSV 或 Excel 文件")
uploaded_file = st.file_uploader("上传账本文件", type=["csv", "xlsx"])
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        else:
            st.error("❌ 文件格式不支持")
            df = None
        if df is not None:
            df = df.reindex(columns=expected_columns)
            df = clean_old_wear_column(df)
            st.session_state.data = df
            st.success("✅ 已加载账本")
    except Exception as e:
        st.error(f"❌ 文件读取失败: {e}")

# ---------- 添加记录 ----------
st.subheader("➕ 添加新记录")
with st.form("new_record"):
    col1, col2, col3 = st.columns(3)
    with col1:
        item = st.text_input("购买物品")
        platform = st.text_input("购买平台")
        wear = st.number_input("磨损", min_value=0.0, max_value=1.0, step=0.01,format="%.3f")
        wear_grade = get_wear_grade(wear)
    with col2:
        buy_price = st.number_input("购入价格", step=0.01)
        buy_date = st.date_input("购入时间")
        sell_price = st.number_input("卖出价格", step=0.01)
    with col3:
        sell_platform = st.text_input("卖出平台")
        fill_sell_date = st.checkbox("是否填写卖出时间？", value=True)
        sell_date = st.date_input("卖出时间") if fill_sell_date else None
        actual_price = st.number_input("实际到手价格", step=0.01)

    if st.form_submit_button("✅ 添加"):
        profit = actual_price - buy_price if actual_price else None
        new_row = pd.DataFrame([[item, platform, wear, wear_grade, buy_price, buy_date,
                                 sell_price, sell_platform, sell_date,
                                 actual_price, profit]], columns=expected_columns)
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.session_state.data.to_csv("cs_log.csv", index=False, encoding='utf-8-sig')
        st.success("记录已添加")
        st.rerun()

# ---------- 搜索 + 排序 ----------
st.subheader("🔍 搜索记录 & 排序")
search_term = st.text_input("输入关键词（购买物品/平台）").lower()
sort_option = st.selectbox("排序方式", ["默认", "按毛利从高到低", "按毛利从低到高"])

filtered_data = st.session_state.data.copy()
if search_term:
    filtered_data = filtered_data[
        filtered_data['购买物品'].astype(str).str.lower().str.contains(search_term, na=False) |
        filtered_data['购买平台'].astype(str).str.lower().str.contains(search_term, na=False)
    ]
if sort_option == "按毛利从高到低":
    filtered_data = filtered_data.sort_values(by="毛利", ascending=False)
elif sort_option == "按毛利从低到高":
    filtered_data = filtered_data.sort_values(by="毛利", ascending=True)

for col in ['购入时间', '卖出时间']:
    filtered_data[col] = pd.to_datetime(filtered_data[col], errors="coerce")

# ---------- 展示记录 ----------
st.subheader("📋 当前账目记录")
if not filtered_data.empty:
    for idx, row in filtered_data.iterrows():
        col1, col2, col3 = st.columns([7, 1, 1])

        if pd.isna(row['实际到手价格']):
            color = "black"
        elif pd.notna(row['毛利']) and row['毛利'] > 0:
            color = "red"
        elif pd.notna(row['毛利']) and row['毛利'] < 0:
            color = "green"
        else:
            color = "black"

        buy_str = f"￥{row['购入价格']:.2f}" if pd.notna(row["购入价格"]) else "—"
        profit_str = f"￥{row['毛利']:.2f}" if pd.notna(row["毛利"]) else "—"
        wear_str = f"{row['磨损']:.3f}（{row['磨损等级']}）" if pd.notna(row['磨损']) else "—"

        with col1:
            st.markdown(
                f"<span style='color:{color}'>【{idx}】{row['购买物品']} | 平台: {row['购买平台']} | 磨损: {wear_str} | 购入: {buy_str} | 毛利: {profit_str}</span>",
                unsafe_allow_html=True
            )
        with col2:
            if st.button("🗑 删除", key=f"del_{idx}"):
                st.session_state.data.drop(index=idx, inplace=True)
                st.session_state.data.reset_index(drop=True, inplace=True)
                st.session_state.data.to_csv("cs_log.csv", index=False, encoding='utf-8-sig')
                st.rerun()
        with col3:
            if st.button("✏ 修改", key=f"edit_{idx}"):
                st.session_state.edit_index = idx
                st.rerun()
else:
    st.info("暂无记录")

# ---------- 修改记录 ----------
if "edit_index" in st.session_state:
    idx = st.session_state.edit_index
    if 0 <= idx < len(st.session_state.data):
        row = st.session_state.data.loc[idx]
        st.subheader(f"📝 修改记录【{idx}】{row['购买物品']}")
        with st.form("edit_form"):
            # ✅ 可修改：磨损、购入价格、卖出价格、卖出平台、卖出时间、实际到手价格
            wear = st.number_input("磨损", value=row["磨损"] if pd.notna(row["磨损"]) else 0.0,
                                   min_value=0.0, max_value=1.0, step=0.001, format="%.3f")
            buy_price = st.number_input("购入价格", value=row["购入价格"] if pd.notna(row["购入价格"]) else 0.0, step=0.01)
            sell_price = st.number_input("卖出价格", value=row["卖出价格"] if pd.notna(row["卖出价格"]) else 0.0, step=0.01)
            sell_platform = st.text_input("卖出平台", value=row["卖出平台"] or "")
            fill_sell_date = st.checkbox("是否填写卖出时间？", value=pd.notna(row["卖出时间"]))
            if fill_sell_date:
                sell_date = st.date_input("卖出时间", value=pd.to_datetime(row["卖出时间"]) if pd.notna(row["卖出时间"]) else pd.to_datetime("today"))
            else:
                sell_date = None

            actual_price = st.number_input("实际到手价格", value=row["实际到手价格"] if pd.notna(row["实际到手价格"]) else 0.0, step=0.01)

            if st.form_submit_button("保存修改"):
                st.session_state.data.at[idx, "磨损"] = wear
                st.session_state.data.at[idx, "磨损等级"] = get_wear_grade(wear)
                st.session_state.data.at[idx, "购入价格"] = buy_price
                st.session_state.data.at[idx, "卖出价格"] = sell_price
                st.session_state.data.at[idx, "卖出平台"] = sell_platform
                st.session_state.data.at[idx, "卖出时间"] = sell_date
                st.session_state.data.at[idx, "实际到手价格"] = actual_price
                if actual_price == 0 or sell_price == 0:
                    st.session_state.data.at[idx, "毛利"] = None
                else:
                    st.session_state.data.at[idx, "毛利"] = actual_price - buy_price


                st.session_state.data.to_csv("cs_log.csv", index=False, encoding='utf-8-sig')
                del st.session_state.edit_index
                st.success("✅ 修改已保存")
                st.rerun()


# ---------- 毛利展示 ----------
total_profit = st.session_state.data['毛利'].sum()
st.metric("💰 总毛利", f"￥{total_profit:.2f}")
