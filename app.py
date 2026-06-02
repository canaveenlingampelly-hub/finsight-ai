import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import base64
import re
from pathlib import Path

st.set_page_config(page_title="FinSight AI", layout="wide")
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def get_base64_image(image_path):
    img_path = Path(image_path)
    if img_path.exists():
        return base64.b64encode(img_path.read_bytes()).decode()
    return None

COLOR_BLUE = "#0B3C75"
COLOR_GREEN = "#12A150"
COLOR_RED = "#E63946"
COLOR_ORANGE = "#FF9800"
COLOR_PURPLE = "#6C3CE9"

st.markdown("""
<style>
.stApp {background:#F4F7FB;}
.block-container {padding-top:0.8rem;padding-left:1.2rem;padding-right:1.2rem;}

.top-header {
background:white;
border-radius:16px;
padding:25px 28px;
margin-top:10px;
box-shadow:0px 4px 18px rgba(0,0,0,0.08);
margin-bottom:16px;
}

.upload-card {
background:white;
border-radius:16px;
padding:18px;
box-shadow:0px 4px 16px rgba(0,0,0,0.08);
margin-bottom:18px;
}

[data-testid="metric-container"] {
background:white;
border-radius:18px;
padding:18px !important;
box-shadow:0px 5px 18px rgba(0,0,0,0.08);
border:1px solid #E5EAF2;
}

[data-testid="metric-container"] label {
font-size:13px !important;
font-weight:700 !important;
color:#0B1F3A !important;
}

[data-testid="metric-container"] div {
font-size:22px !important;
font-weight:800 !important;
color:#0B3C75 !important;
}

button[data-baseweb="tab"] {
background:white !important;
border-radius:12px !important;
font-weight:700 !important;
font-size:14px !important;
padding:10px 14px !important;
margin-right:6px !important;
}

.insight-box {
background:linear-gradient(135deg,#FFFFFF,#EEF6FF);
border-left:6px solid #0B3C75;
padding:22px;
border-radius:18px;
box-shadow:0px 5px 18px rgba(0,0,0,0.08);
color:#0B1F3A;
font-size:16px;
}

.cfo-insights-container {
background:#ffffff;
border-radius:18px;
padding:18px 22px;
margin-top:14px;
box-shadow:0px 5px 18px rgba(0,0,0,0.08);
max-height:720px;
overflow:auto;
font-size:0.95rem;
line-height:1.45;
}

.cfo-insights-container h3 {
margin-top:1rem;
margin-bottom:0.35rem;
font-size:1rem;
color:#0B3C75;
}

.cfo-insights-container ul {
margin:0.4rem 0 1rem 1.3rem;
padding-left:0;
}

.cfo-insights-container li {
margin-bottom:0.3rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="top-header">
    <div style="display:flex;align-items:center;gap:20px;">
        <div style="
        width:68px;height:68px;border-radius:50%;
        background:linear-gradient(135deg,#0B3C75,#2563EB);
        display:flex;align-items:center;justify-content:center;
        color:white;font-size:28px;font-weight:bold;">
        FI
        </div>
        <div>
            <div style="font-size:32px;font-weight:900;color:#0B1F3A;line-height:1.2;">FinSight AI</div>
            <div style="font-size:16px;color:#334155;">AI-Powered Financial Intelligence for CFOs, CEOs and Business Leaders</div>
        </div>
        <div style="margin-left:auto;background:#0B3C75;color:white;padding:14px 22px;border-radius:12px;font-weight:700;">
            Financial Dashboard
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

ai_bg = get_base64_image("ai_bg.png")

if ai_bg:
    st.markdown(f"""
    <div style="
    background:
    linear-gradient(90deg, rgba(255,255,255,0.98) 0%, rgba(255,255,255,0.92) 45%, rgba(255,255,255,0.30) 100%),
    url('data:image/png;base64,{ai_bg}');
    background-size:cover;
    background-position:center right;
    padding:38px;
    border-radius:22px;
    margin-bottom:20px;
    box-shadow:0px 6px 20px rgba(0,0,0,0.08);
    border-left:8px solid #0B3C75;
    ">
    <h1 style="color:#0B1F3A;font-size:38px;font-weight:800;margin-bottom:10px;">
    Transforming Financial Data into Executive Decisions
    </h1>
    <p style="font-size:18px;color:#475569;margin-bottom:0px;">
    From 8 Hours of Financial Reporting to a Single Click
    </p>
    <p style="font-size:14px;color:#6B7280;font-weight:500;margin-top:5px;margin-bottom:0px;">
    Board Reporting • Variance Analysis • Working Capital • Banking Covenants • AI Advisory
    </p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.warning("ai_bg.png not found in app.py folder.")

try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=gemini_api_key)
    gemini_ready = True
except Exception:
    gemini_ready = False

def clean_number(series):
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.strip()
        .replace("", "0")
        .replace("nan", "0")
        .astype(float)
    )

def get_value(df, kpi_type, column="Actual"):
    return abs(df[df["KPI Type"].astype(str).str.strip() == kpi_type][column].sum())

def format_cr(value):
    return f"₹{value / 10000000:,.2f} Cr"

def to_cr(value):
    return value / 10000000

def variance_status(row):
    kpi = str(row["KPI Type"]).strip()
    variance = row["Actual"] - row["Budget"]

    income_types = ["Revenue", "Other Income"]
    expense_types = ["COGS", "Other Expense", "Interest", "Depreciation", "Tax"]

    if kpi in income_types:
        return "🟢 ▲ Favourable" if variance >= 0 else "🔴 ▼ Unfavourable"

    if kpi in expense_types:
        return "🟢 ▼ Favourable" if variance <= 0 else "🔴 ▲ Unfavourable"

    return "Neutral"


def format_insight_html(text):
    lines = [line.rstrip() for line in text.strip().splitlines()]
    html_lines = []
    in_list = False

    for line in lines:
        if line.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{line[4:].strip()}</h3>")
        elif line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{line[2:].strip()}</li>")
        elif line == "":
            if in_list:
                html_lines.append("</ul>")
                in_list = False
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{line}</p>")

    if in_list:
        html_lines.append("</ul>")

    return '<div class="cfo-insights-container">' + "".join(html_lines) + '</div>'


def build_interactive_prompt(question, metrics, top_variance_text, top_states_text, top_products_text):
    return f"""
You are a senior finance advisor. Use only the data provided below and do not assume any missing financials.
Answer the user's question clearly and provide practical recommendations if the query is about improvements, risks, or next steps.
If the question is not related to the uploaded financial data, say: "I can only answer questions related to the uploaded financial dataset."

Data Summary:
{metrics}

Top P&L Variances:
{top_variance_text}

Top Sales States:
{top_states_text}

Top Products by Sales:
{top_products_text}

Question: {question}

Answer format:
- One short paragraph or bullet list.
- If the question asks for recommendations, include at least one practical action.
"""

st.markdown('<div class="upload-card">', unsafe_allow_html=True)
st.markdown("### 📁 Financial Data Hub")
st.caption("Upload Trial Balance, Sales Register and Receivable Ageing to generate executive finance insights.")

u1, u2, u3 = st.columns(3)

with u1:
    tb_file = st.file_uploader("Trial Balance", type=["xlsx"], key="tb")

with u2:
    sales_file = st.file_uploader("Sales Register", type=["xlsx"], key="sales")

with u3:
    recv_file = st.file_uploader("Receivable Ageing", type=["xlsx"], key="recv")

st.markdown("</div>", unsafe_allow_html=True)

if tb_file and sales_file and recv_file:

    tb_raw = pd.read_excel(tb_file, sheet_name="TB", header=None)

    header_row = None
    for i in range(min(15, len(tb_raw))):
        row_values = tb_raw.iloc[i].astype(str).str.strip().tolist()
        if "Actual" in row_values and "Budget" in row_values:
            header_row = i
            break

    if header_row is None:
        st.error("Could not find Actual and Budget columns in Trial Balance.")
        st.stop()

    tb_df = pd.read_excel(tb_file, sheet_name="TB", header=header_row)
    tb_df.columns = tb_df.columns.astype(str).str.strip()

    try:
        sales_df = pd.read_excel(sales_file, sheet_name="Sales Register ", header=1)
    except Exception:
        sales_df = pd.read_excel(sales_file, sheet_name=0, header=1)

    sales_df.columns = sales_df.columns.astype(str).str.strip()

    try:
        recv_df = pd.read_excel(recv_file, sheet_name="Receivable Ageing ", header=1)
    except Exception:
        recv_df = pd.read_excel(recv_file, sheet_name=0, header=1)

    recv_df.columns = recv_df.columns.astype(str).str.strip()

    required_tb_cols = ["GL Description", "Category", "KPI Type", "Actual", "Budget"]
    required_sales_cols = ["Sales", "Qty", "State", "Product Name"]
    required_recv_cols = ["Outstanding", "Days"]

    missing_tb = [c for c in required_tb_cols if c not in tb_df.columns]
    missing_sales = [c for c in required_sales_cols if c not in sales_df.columns]
    missing_recv = [c for c in required_recv_cols if c not in recv_df.columns]

    if missing_tb:
        st.error(f"Missing columns in Trial Balance: {missing_tb}")
        st.write("TB columns found:", tb_df.columns.tolist())
        st.stop()

    if missing_sales:
        st.error(f"Missing columns in Sales Register: {missing_sales}")
        st.write("Sales columns found:", sales_df.columns.tolist())
        st.stop()

    if missing_recv:
        st.error(f"Missing columns in Receivable Ageing: {missing_recv}")
        st.write("Receivable columns found:", recv_df.columns.tolist())
        st.stop()

    tb_df["Actual"] = clean_number(tb_df["Actual"])
    tb_df["Budget"] = clean_number(tb_df["Budget"])

    tb_df["Actual"] = tb_df["Actual"].abs()
    tb_df["Budget"] = tb_df["Budget"].abs()
    sales_df["Sales"] = clean_number(sales_df["Sales"])
    sales_df["Qty"] = clean_number(sales_df["Qty"])
    recv_df["Outstanding"] = clean_number(recv_df["Outstanding"])
    recv_df["Days"] = clean_number(recv_df["Days"])

    revenue = get_value(tb_df, "Revenue")
    other_income = get_value(tb_df, "Other Income")
    cogs = get_value(tb_df, "COGS")
    other_expense = get_value(tb_df, "Other Expense")
    interest = get_value(tb_df, "Interest")
    depreciation = get_value(tb_df, "Depreciation")
    tax = get_value(tb_df, "Tax")
    cash = get_value(tb_df, "Cash")
    receivable = get_value(tb_df, "Receivable")
    inventory = get_value(tb_df, "Inventory")
    payable = get_value(tb_df, "Payable")
    debt = get_value(tb_df, "Debt")
    equity = get_value(tb_df, "Equity")
    principal = get_value(tb_df, "Principal")

    gross_profit = revenue - cogs
    ebitda = revenue + other_income - cogs - other_expense
    ebit = ebitda - depreciation
    pbt = ebit - interest
    pat = pbt - tax

    total_sales = sales_df["Sales"].sum()
    total_qty = sales_df["Qty"].sum()
    total_receivables = recv_df["Outstanding"].sum()
    receivables_90 = recv_df[recv_df["Days"] >= 90]["Outstanding"].sum()
    risk_percent = (receivables_90 / total_receivables) * 100 if total_receivables else 0

    top_states = (
        sales_df.groupby("State")["Sales"].sum()
        .reset_index()
        .sort_values("Sales", ascending=False)
        .head(5)
    )
    top_products = (
        sales_df.groupby("Product Name")["Sales"].sum()
        .reset_index()
        .sort_values("Sales", ascending=False)
        .head(5)
    )

    dso = (receivable / revenue) * 365 if revenue else 0
    dio = (inventory / cogs) * 365 if cogs else 0
    dpo = (payable / cogs) * 365 if cogs else 0
    ccc = dso + dio - dpo
    nwc = receivable + inventory - payable

    interest_coverage = ebit / interest if interest else 0
    dscr = (pat + depreciation + interest) / (interest + principal) if (interest + principal) else 0
    debt_equity = debt / equity if equity else 0
    net_debt_ebitda = (debt - cash) / ebitda if ebitda else 0

    tb_df["Variance"] = tb_df["Actual"] - tb_df["Budget"]
    tb_df["Variance Cr"] = tb_df["Variance"] / 10000000
    tb_df["Actual Cr"] = tb_df["Actual"] / 10000000
    tb_df["Budget Cr"] = tb_df["Budget"] / 10000000
    tb_df["Variance %"] = tb_df.apply(
        lambda x: round((x["Variance"] / x["Budget"] * 100), 0) if x["Budget"] != 0 else 0,
        axis=1
    )
    tb_df["Status"] = tb_df.apply(variance_status, axis=1)

    top_ai_variance = tb_df[
        tb_df["KPI Type"].isin([
            "Revenue", "COGS", "Other Income",
            "Other Expense", "Interest", "Depreciation", "Tax"
        ])
    ].sort_values("Variance Cr", key=abs, ascending=False).head(10).copy()

    st.markdown("### KPI Snapshot")
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Revenue", format_cr(revenue))
    s2.metric("EBITDA", format_cr(ebitda))
    s3.metric("PAT", format_cr(pat))
    s4.metric("CCC", f"{ccc:.0f} Days")
    s5.metric("DSCR", f"{dscr:.2f}x")
    revenue_budget = get_value(tb_df, "Revenue", "Budget")

    ebitda_budget = (
        get_value(tb_df, "Revenue", "Budget")
        + get_value(tb_df, "Other Income", "Budget")
        - get_value(tb_df, "COGS", "Budget")
        - get_value(tb_df, "Other Expense", "Budget")
    )
    
    pat_budget = (
        ebitda_budget
        - get_value(tb_df, "Depreciation", "Budget")
        - get_value(tb_df, "Interest", "Budget")
        - get_value(tb_df, "Tax", "Budget")
    )
    
    revenue_var_pct = ((revenue - revenue_budget) / revenue_budget * 100) if revenue_budget else 0
    ebitda_var_pct = ((ebitda - ebitda_budget) / ebitda_budget * 100) if ebitda_budget else 0
    pat_var_pct = ((pat - pat_budget) / pat_budget * 100) if pat_budget else 0
    
    rev_color = "green" if revenue_var_pct >= 0 else "red"
    ebitda_color = "green" if ebitda_var_pct >= 0 else "red"
    pat_color = "green" if pat_var_pct >= 0 else "red"
    
    rev_text = "UP" if revenue_var_pct >= 0 else "DOWN"
    ebitda_text = "UP" if ebitda_var_pct >= 0 else "DOWN"
    pat_text = "UP" if pat_var_pct >= 0 else "DOWN"
    
    st.markdown(
        f"""
        <div style="
        background:white;
        padding:12px;
        border-radius:12px;
        margin-top:10px;
        margin-bottom:15px;
        font-size:16px;
        font-weight:600;
        box-shadow:0px 3px 10px rgba(0,0,0,0.08);
        ">
    
        ⬆ Revenue is <span style='color:{rev_color}'>{rev_text} by {abs(revenue_var_pct):.1f}%</span> vs Budget |
        ⬆ EBITDA is <span style='color:{ebitda_color}'>{ebitda_text} by {abs(ebitda_var_pct):.1f}%</span> vs Budget |
        ⬆ PAT is <span style='color:{pat_color}'>{pat_text} by {abs(pat_var_pct):.1f}%</span> vs Budget
    
        </div>
        """,
        unsafe_allow_html=True
    )
    
    tab0, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "★ Executive Dashboard",
            "◈ Sales Dynamics",
            "⚖ Variance Analysis",
            "◉ Working Capital & Risk",
            "★ AI Board Advisor",
            "✦ Interactive AI"
        ])
    
    with tab0:
            st.header("Executive Dashboard")
    
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Revenue", format_cr(revenue))
            c2.metric("Gross Profit", format_cr(gross_profit))
            c3.metric("EBITDA", format_cr(ebitda))
            c4.metric("PAT", format_cr(pat))
    
            c5, c6, c7, c8 = st.columns(4)
            c5.metric("EBITDA Margin", f"{(ebitda / revenue * 100) if revenue else 0:.0f}%")
            c6.metric("PAT Margin", f"{(pat / revenue * 100) if revenue else 0:.0f}%")
            c7.metric("Finance Cost", format_cr(interest))
            c8.metric("Tax", format_cr(tax))
    
            r1, r2, r3, r4 = st.columns(4)
            r1.success(f"CCC: {ccc:.0f} Days")
    
            if risk_percent > 25:
                r2.error(f"Receivable Risk: {risk_percent:.0f}%")
            else:
                r2.warning(f"Receivable Risk: {risk_percent:.0f}%")
    
            r3.success(f"DSCR: {dscr:.2f}x")
            r4.success(f"Interest Coverage: {interest_coverage:.2f}x")
    
            c1, c2, c3 = st.columns(3)
    
            with c1:
                prof_df = pd.DataFrame({
                    "Metric": ["Revenue", "EBITDA", "PAT"],
                    "Amount Cr": [to_cr(revenue), to_cr(ebitda), to_cr(pat)]
                })
    
                fig = px.bar(
                    prof_df,
                    x="Metric",
                    y="Amount Cr",
                    title="Revenue vs Profitability (₹ Cr)",
                    color="Metric",
                    color_discrete_sequence=[COLOR_BLUE, COLOR_GREEN, COLOR_PURPLE]
                )
                fig.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
    
            with c2:
                wc_df = pd.DataFrame({
                    "Type": ["Receivables", "Inventory", "Payables"],
                    "Amount Cr": [to_cr(receivable), to_cr(inventory), to_cr(payable)]
                })
    
                fig = px.pie(
                    wc_df,
                    names="Type",
                    values="Amount Cr",
                    hole=0.50,
                    title="Working Capital Snapshot (₹ Cr)",
                    color_discrete_sequence=[COLOR_BLUE, COLOR_GREEN, COLOR_ORANGE]
                )
                fig.update_layout(height=380, paper_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
    
            with c3:
                expense_df = tb_df[
                    tb_df["KPI Type"].isin(["COGS", "Other Expense", "Interest", "Depreciation", "Tax"])
                ]
                top_exp = expense_df.sort_values("Actual Cr", ascending=False).head(5)
    
                fig = px.bar(
                    top_exp,
                    x="Actual Cr",
                    y="GL Description",
                    orientation="h",
                    title="Top 5 Expense Drivers (₹ Cr)",
                    color="KPI Type",
                    color_discrete_sequence=[COLOR_BLUE, COLOR_GREEN, COLOR_ORANGE, COLOR_PURPLE, COLOR_RED]
                )
                fig.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white", yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
            st.header("Sales Dynamics and Geographic Insights")
    
            c1, c2 = st.columns(2)
            c1.metric("Sales Register Value", format_cr(total_sales))
            c2.metric("Total Quantity", f"{total_qty:,.0f}")
    
            s1, s2 = st.columns(2)
    
            with s1:
                state_sales = sales_df.groupby("State")["Sales"].sum().reset_index().sort_values("Sales", ascending=False).head(10)
                state_sales["Sales Cr"] = state_sales["Sales"] / 10000000
    
                fig = px.bar(
                    state_sales,
                    x="Sales Cr",
                    y="State",
                    orientation="h",
                    title="Top 10 States by Sales (₹ Cr)",
                    color="Sales Cr",
                    color_continuous_scale="Blues"
                )
                fig.update_layout(height=420, plot_bgcolor="white", paper_bgcolor="white", yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig, use_container_width=True)
    
            with s2:
                product_sales = sales_df.groupby("Product Name")["Sales"].sum().reset_index().sort_values("Sales", ascending=False).head(10)
                product_sales["Sales Cr"] = product_sales["Sales"] / 10000000
    
                fig = px.bar(
                    product_sales,
                    x="Sales Cr",
                    y="Product Name",
                    orientation="h",
                    title="Top 10 Products by Sales (₹ Cr)",
                    color="Sales Cr",
                    color_continuous_scale="Greens"
                )
                fig.update_layout(height=420, plot_bgcolor="white", paper_bgcolor="white", yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
            st.header("Variance Analysis")
    
            pl_variance = tb_df[
                tb_df["KPI Type"].isin([
                    "Revenue", "COGS", "Other Income",
                    "Other Expense", "Interest", "Depreciation", "Tax"
                ])
            ].copy()
    
            budget_revenue = get_value(tb_df, "Revenue", "Budget")
            revenue_variance = revenue - budget_revenue
    
            budget_ebitda = (
                get_value(tb_df, "Revenue", "Budget")
                + get_value(tb_df, "Other Income", "Budget")
                - get_value(tb_df, "COGS", "Budget")
                - get_value(tb_df, "Other Expense", "Budget")
            )
    
            ebitda_variance = ebitda - budget_ebitda
    
            c1, c2 = st.columns(2)
            c1.metric("Revenue Variance", format_cr(revenue_variance))
            c2.metric("EBITDA Variance", format_cr(ebitda_variance))
    
            top_var = pl_variance.sort_values("Variance Cr", key=abs, ascending=False).head(15)
    
            fig = px.bar(
                top_var,
                x="Variance Cr",
                y="GL Description",
                orientation="h",
                color="Status",
                title="Top P&L Budget Variances (₹ Cr)",
                color_discrete_map={
                    "🟢 ▲ Favourable": COLOR_GREEN,
                    "🟢 ▼ Favourable": COLOR_GREEN,
                    "🔴 ▲ Unfavourable": COLOR_RED,
                    "🔴 ▼ Unfavourable": COLOR_RED
                }
                
            )
            fig.update_layout(height=520, plot_bgcolor="white", paper_bgcolor="white", yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)
    
            display_variance = pl_variance[
                ["GL Description", "KPI Type", "Actual Cr", "Budget Cr", "Variance Cr", "Variance %", "Status"]
            ].copy()
    
            display_variance["Actual Cr"] = display_variance["Actual Cr"].round(2)
            display_variance["Budget Cr"] = display_variance["Budget Cr"].round(2)
            display_variance["Variance Cr"] = display_variance["Variance Cr"].round(2)
            display_variance["Variance %"] = display_variance["Variance %"].astype(int).astype(str) + "%"
    
            st.dataframe(display_variance, use_container_width=True)
    
    with tab4:
            st.header("Working Capital & Banking Covenants")
    
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("DSO", f"{dso:.0f} Days")
            c2.metric("DIO", f"{dio:.0f} Days")
            c3.metric("DPO", f"{dpo:.0f} Days")
            c4.metric("CCC", f"{ccc:.0f} Days")
            c5.metric("NWC", format_cr(nwc))
    
            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Interest Coverage", f"{interest_coverage:.2f}x")
            b2.metric("DSCR", f"{dscr:.2f}x")
            b3.metric("Debt / Equity", f"{debt_equity:.2f}x")
            b4.metric("Net Debt / EBITDA", f"{net_debt_ebitda:.2f}x")
    
            recv_df["Ageing Bucket"] = pd.cut(
                recv_df["Days"],
                bins=[0, 30, 60, 90, 9999],
                labels=["0-30", "31-60", "61-90", ">90"],
                include_lowest=True
            )
    
            w1, w2 = st.columns(2)
    
            with w1:
                ageing = recv_df.groupby("Ageing Bucket", observed=False)["Outstanding"].sum().reset_index()
                ageing["Outstanding Cr"] = ageing["Outstanding"] / 10000000
    
                fig = px.bar(
                    ageing,
                    x="Ageing Bucket",
                    y="Outstanding Cr",
                    color="Ageing Bucket",
                    title="Receivable Ageing Bucket (₹ Cr)",
                    color_discrete_sequence=[COLOR_GREEN, COLOR_BLUE, COLOR_ORANGE, COLOR_RED]
                )
                fig.update_layout(height=420, plot_bgcolor="white", paper_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
    
            with w2:
                covenant_data = pd.DataFrame({
                    "Metric": ["Interest Coverage", "DSCR", "Debt / Equity", "Net Debt / EBITDA"],
                    "Value": [interest_coverage, dscr, debt_equity, net_debt_ebitda]
                })
    
                fig = px.bar(
                    covenant_data,
                    x="Metric",
                    y="Value",
                    color="Metric",
                    title="Banking Covenant Ratios",
                    color_discrete_sequence=[COLOR_BLUE, COLOR_GREEN, COLOR_ORANGE, COLOR_RED]
                )
                fig.update_layout(height=420, plot_bgcolor="white", paper_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
    
    with tab5:
            st.header("★ AI Board Advisor")

            if "insight_text" not in st.session_state:
                st.session_state["insight_text"] = ""

            if st.button("Generate CFO Insights", type="primary"):

                top_ai_variance = tb_df[
                    tb_df["KPI Type"].isin([
                        "Revenue", "COGS", "Other Income",
                        "Other Expense", "Interest", "Depreciation", "Tax"
                    ])
                ].sort_values("Variance Cr", key=abs, ascending=False).head(10)

                revenue_budget = get_value(tb_df, "Revenue", "Budget")
                revenue_variance = revenue - revenue_budget
                revenue_variance_pct = (revenue_variance / revenue_budget * 100) if revenue_budget else 0
                ebitda_margin = (ebitda / revenue * 100) if revenue else 0
                pat_margin = (pat / revenue * 100) if revenue else 0

                prompt = f"""
    You are a Group CFO, Board Advisor, Credit Analyst and Business Partner.

    Use ONLY the figures provided. Do NOT assume or create any numbers.

    Executive Metrics:
    Revenue Actual: {format_cr(revenue)}
    Revenue Budget: {format_cr(revenue_budget)}
    Revenue Variance: {format_cr(revenue_variance)}
    Revenue Variance %: {revenue_variance_pct:.1f}%

    Gross Profit: {format_cr(gross_profit)}
    EBITDA: {format_cr(ebitda)}
    EBITDA Margin: {ebitda_margin:.1f}%
    PAT: {format_cr(pat)}
    PAT Margin: {pat_margin:.1f}%

    Working Capital:
    Receivables: {format_cr(receivable)}
    Inventory: {format_cr(inventory)}
    Payables: {format_cr(payable)}
    DSO: {dso:.0f} days
    DIO: {dio:.0f} days
    DPO: {dpo:.0f} days
    CCC: {ccc:.0f} days

    Banking Covenants:
    Interest Coverage: {interest_coverage:.2f}x
    DSCR: {dscr:.2f}x
    Debt Equity: {debt_equity:.2f}x
    Net Debt EBITDA: {net_debt_ebitda:.2f}x

    Receivable Risk:
    Total Receivables: {format_cr(total_receivables)}
    Receivables above 90 days: {format_cr(receivables_90)}
    Receivable Risk %: {risk_percent:.0f}%

    Top P&L Variances:
    {top_ai_variance[["GL Description", "KPI Type", "Actual Cr", "Budget Cr", "Variance Cr", "Variance %", "Status"]].to_string(index=False)}

    Prepare CFO Insights in this EXACT format only.

    ## ➤ CURRENT POSITION
    - Maximum 3 bullet points.
    - Explain the current financial position using Revenue, EBITDA, PAT, EBITDA Margin, PAT Margin, CCC, DSCR and Interest Coverage.
    - Mention whether the company is financially strong, stable, stretched or risky based only on the figures provided.

    ## ◈ ACHIEVEMENTS
    - Maximum 3 bullet points.
    - Mention positive performance areas only.
    - Compare Actual vs Budget wherever available.
    - Highlight revenue performance, profitability, covenant comfort and working capital strengths.

    ## ⬆ KEY RISKS
    - Maximum 3 bullet points.
    - Mention financial risks, profitability risks, working capital risks, receivable ageing risks and covenant risks.
    - Quantify each risk wherever data is available.
    - If no major covenant risk exists, clearly write: "No major covenant risk identified, but continuous monitoring is required."

    ## ✔ CFO RECOMMENDATIONS
    - Maximum 3 bullet points.
    - Give practical CFO-level actions.
    - Focus on collections, cost control, margin improvement, cash flow discipline, budgeting and business performance.
    - Each recommendation must start with an action verb.

    STRICT RULES:
    - Do NOT write any introduction.
    - Do NOT write "As Group CFO..." or similar opening sentence.
    - Do NOT write paragraphs.
    - Use ONLY the 4 headings above.
    - Use bullet points only.
    - Complete all 4 sections.
    - Keep each bullet to one line.
    - Avoid generic advice.
    - Be specific, quantitative and practical.
    """

                if gemini_ready:
                    try:
                        model = genai.GenerativeModel("gemini-2.5-flash")

                        with st.spinner("🤖 Generating board-level insights..."):
                            response = model.generate_content(
                                prompt,
                                generation_config={
                                    "temperature": 0.2,
                                    "max_output_tokens": 5000,
                                }
                            )

                        insight_text = response.text

                    except Exception as e:
                        insight_text = f"""
    ### Gemini API Issue
    Gemini could not generate live AI insights.

    Reason:
    {e}

    ### Fallback CFO Insights
    Revenue is {format_cr(revenue)} against budget of {format_cr(revenue_budget)}, with variance of {format_cr(revenue_variance)} ({revenue_variance_pct:.1f}%).

    EBITDA is {format_cr(ebitda)} with EBITDA margin of {ebitda_margin:.1f}%.

    PAT is {format_cr(pat)} with PAT margin of {pat_margin:.1f}%.

    DSO is {dso:.0f} days, CCC is {ccc:.0f} days, DSCR is {dscr:.2f}x and Interest Coverage is {interest_coverage:.2f}x.

    ### Key Actions
    - Review top unfavourable P&L variances.
    - Reduce receivable ageing above 90 days.
    - Improve cash conversion cycle.
    - Monitor DSCR and interest coverage monthly.
    """

                else:
                    insight_text = f"""
    ### CFO Insights

    Revenue is {format_cr(revenue)} against budget of {format_cr(revenue_budget)}, with variance of {format_cr(revenue_variance)} ({revenue_variance_pct:.1f}%).

    EBITDA is {format_cr(ebitda)} with EBITDA margin of {ebitda_margin:.1f}%.

    PAT is {format_cr(pat)} with PAT margin of {pat_margin:.1f}%.

    ### Key Risks
    - DSO is {dso:.0f} days.
    - CCC is {ccc:.0f} days.
    - Receivables above 90 days are {format_cr(receivables_90)}.
    - DSCR is {dscr:.2f}x.

    ### Action Plan
    - Reduce receivable ageing.
    - Monitor top P&L variances.
    - Improve cash conversion cycle.
    - Track DSCR and interest coverage monthly.
    """

                st.session_state["insight_text"] = insight_text

            st.markdown("### ✨ Boardroom AI Insights")
            if st.session_state["insight_text"]:
                insight_html = format_insight_html(st.session_state["insight_text"])
                st.markdown(insight_html, unsafe_allow_html=True)
            else:
                st.info("Click Generate CFO Insights to create boardroom-level commentary.")

    with tab6:
            st.header("✦ Interactive AI Q&A")
            st.markdown("Ask questions about the uploaded financial dataset and get data-driven recommendations.")

            if "interactive_question" not in st.session_state:
                st.session_state["interactive_question"] = ""
            if "interactive_response" not in st.session_state:
                st.session_state["interactive_response"] = ""

            user_question = st.text_area(
                "Ask your question",
                value=st.session_state["interactive_question"],
                placeholder="e.g. What is the biggest cash risk? How can we improve receivables?",
                height=140,
                key="interactive_question"
            )

            if st.button("Ask AI", type="primary"):
                if not user_question.strip():
                    st.warning("Please enter a question before asking the AI.")
                else:
                    metrics_text = (
                        f"Revenue Actual: {format_cr(revenue)}\n"
                        f"Revenue Budget: {format_cr(revenue_budget)}\n"
                        f"EBITDA: {format_cr(ebitda)}\n"
                        f"PAT: {format_cr(pat)}\n"
                        f"DSO: {dso:.0f} days\n"
                        f"CCC: {ccc:.0f} days\n"
                        f"DSCR: {dscr:.2f}x\n"
                        f"Interest Coverage: {interest_coverage:.2f}x\n"
                        f"Receivables: {format_cr(receivable)}\n"
                        f"Receivables >90 days: {format_cr(receivables_90)} ({risk_percent:.0f}% risk)\n"
                    )

                    top_variance_text = "\n".join(
                        top_ai_variance["GL Description"].astype(str)
                        + ": "
                        + top_ai_variance["KPI Type"].astype(str)
                        + ", Actual Cr="
                        + top_ai_variance["Actual Cr"].round(2).astype(str)
                        + ", Budget Cr="
                        + top_ai_variance["Budget Cr"].round(2).astype(str)
                        + ", Var Cr="
                        + top_ai_variance["Variance Cr"].round(2).astype(str)
                        + ", Status="
                        + top_ai_variance["Status"].astype(str)
                    )

                    top_states_text = "\n".join(
                        top_states["State"].astype(str)
                        + ": "
                        + top_states["Sales"].div(10000000).round(2).astype(str)
                        + " Cr"
                    )

                    top_products_text = "\n".join(
                        top_products["Product Name"].astype(str)
                        + ": "
                        + top_products["Sales"].div(10000000).round(2).astype(str)
                        + " Cr"
                    )

                    prompt = build_interactive_prompt(
                        user_question,
                        metrics_text,
                        top_variance_text,
                        top_states_text,
                        top_products_text,
                    )

                    if gemini_ready:
                        try:
                            model = genai.GenerativeModel("gemini-2.5-flash")
                            with st.spinner("🤖 Answering your financial question..."):
                                response = model.generate_content(
                                    prompt,
                                    generation_config={
                                        "temperature": 0.2,
                                        "max_output_tokens": 1200,
                                    }
                                )
                            st.session_state["interactive_response"] = response.text.strip()
                        except Exception as e:
                            st.session_state["interactive_response"] = (
                                "Gemini API issue: "
                                + str(e)
                                + "\n\nPlease check your API key or try again later."
                            )
                    else:
                        st.session_state["interactive_response"] = (
                            "Gemini API is not configured. Please add GEMINI_API_KEY to Streamlit secrets. "
                            "Until then, use the AI Board Advisor tab for high-level insights."
                        )

            if st.session_state["interactive_response"]:
                st.markdown("### AI Answer")
                st.markdown(st.session_state["interactive_response"])
            else:
                st.info("Type a question about your uploaded data and click Ask AI.")
    
else:
    st.warning("Please upload Trial Balance, Sales Register and Receivable Ageing files.")
