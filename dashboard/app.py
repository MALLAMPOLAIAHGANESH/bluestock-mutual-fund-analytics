"""
dashboard/app.py
================
Bluestock MF Capstone — Executive Summary Dashboard (V3 Premium Theme)
"""
# pyrefly: ignore [missing-import]
import streamlit as st
import os
import pandas as pd
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Executive Summary | Bluestock MF Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Apply Custom CSS ──
def load_css():
    css_path = Path(__file__).resolve().parent.parent / 'style.css' if 'pages' in str(Path(__file__).resolve()) else Path(__file__).resolve().parent / 'style.css'
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
load_css()

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"

# ── Load Data with Caching ──
@st.cache_data
def load_summary_data():
    fm = pd.read_csv(DATA / "01_fund_master.csv")
    perf = pd.read_csv(DATA / "07_scheme_performance.csv")
    bench = pd.read_csv(DATA / "10_benchmark_indices.csv", parse_dates=["date"])
    txns = pd.read_csv(DATA / "08_investor_transactions.csv", parse_dates=["transaction_date"])
    return fm, perf, bench, txns

try:
    fm, perf, bench, txns = load_summary_data()
    data_loaded = True
except Exception as e:
    st.error(f"Error loading datasets: {e}")
    data_loaded = False

# ── Sidebar branding ──
with st.sidebar:
    st.image("https://img.icons8.com/color/96/stock-market.png", width=80)
    st.title("Bluestock MF")
    st.caption("Mutual Fund Analytics Platform")
    st.divider()
    st.info("**Navigate** using the pages below.\n\nAll charts are **interactive**.")
    st.divider()
    st.caption("Data: 40 AMFI schemes · Jan 2022 – Dec 2025")
    st.caption("Bluestock Fintech Capstone Project")
    st.divider()
    st.markdown("""
    **👨‍💻 Author**  
    **Mallam Polaiah Ganesh**  
    *Aspiring Data Analyst | Data Science Enthusiast | Python | SQL | Power BI | Machine Learning*

    🔗 [GitHub](https://github.com/MALLAMPOLAIAHGANESH)  
    🔗 [LinkedIn](https://www.linkedin.com/in/mallam-polaiah-ganesh-b33748218/)
    """)

# ── Main Content ──
st.title("📈 Executive Summary Dashboard")
st.markdown("### Welcome to the Interactive Portfolio Analytics & Business Intelligence Portal")

if data_loaded:
    # ── Calculation of Dynamic Metrics ──
    total_aum = perf["aum_crore"].sum()
    total_funds = perf["scheme_name"].nunique()
    total_fund_houses = perf["fund_house"].nunique()
    avg_cagr_3y = perf["return_3yr_pct"].mean()
    avg_expense = perf["expense_ratio_pct"].mean()
    
    # Best performing fund (3Y CAGR)
    best_fund_row = perf.loc[perf["return_3yr_pct"].idxmax()]
    best_fund_name = best_fund_row["scheme_name"]
    best_fund_ret = best_fund_row["return_3yr_pct"]
    
    # Lowest risk fund (Annualized Std Dev)
    lowest_risk_row = perf.loc[perf["std_dev_ann_pct"].idxmin()]
    lowest_risk_name = lowest_risk_row["scheme_name"]
    lowest_risk_val = lowest_risk_row["std_dev_ann_pct"]
    
    # Portfolio Health Score: % of funds with positive Sharpe ratio & positive return
    healthy_funds = perf[(perf["sharpe_ratio"] > 0.8) & (perf["return_3yr_pct"] > 6.5)]
    health_score = (len(healthy_funds) / len(perf)) * 100

    # ── KPI Cards ──
    st.markdown("#### Key Performance Indicators (KPIs)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total AUM", f"₹ {total_aum:,.0f} Cr", help="Total Assets Under Management across all schemes")
    col2.metric("Total Funds", f"{total_funds}", help="Total active schemes analyzed")
    col3.metric("Fund Houses", f"{total_fund_houses}", help="Total Asset Management Companies (AMCs) represented")
    col4.metric("Portfolio Health Score", f"{health_score:.1f}%", help="Percentage of funds with Sharpe > 0.8 and Return > 6.5% (risk-free rate)")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Avg 3Y Return (CAGR)", f"{avg_cagr_3y:.2f}%", help="Average 3-year compound annual growth rate")
    col6.metric("Avg Expense Ratio", f"{avg_expense:.2f}%", help="Average annual fee charged to investors")
    col7.metric("Top Performing Scheme", f"{best_fund_ret:.1f}% Return", help=f"Best fund: {best_fund_name}")
    col8.metric("Lowest Volatility Scheme", f"{lowest_risk_val:.1f}% Std Dev", help=f"Lowest risk fund: {lowest_risk_name}")

    st.divider()

    # ── Tabs layout ──
    tab_summary, tab_nav, tab_dl, tab_nb = st.tabs([
        "📊 Market Snapshot & Analysis", 
        "🏠 Navigation Guide", 
        "💾 Download Data Assets", 
        "📓 Jupyter Notebooks"
    ])

    with tab_summary:
        st.markdown("#### Cumulative Market Index growth (Jan 2022 - Dec 2025)")
        # Calculate cumulative returns of benchmarks starting at 100
        bench_pivot = bench.pivot(index="date", columns="index_name", values="close_value").dropna()
        normalized_bench = (bench_pivot / bench_pivot.iloc[0]) * 100
        normalized_bench = normalized_bench.reset_index().melt(id_vars="date", value_name="Cumulative Value", var_name="Index Name")

        fig_bench = px.line(
            normalized_bench,
            x="date",
            y="Cumulative Value",
            color="Index Name",
            title="Benchmark Performance Comparison (Base 100 on Jan 2022)",
            color_discrete_sequence=["#dea11a", "#742a10", "#6482a0", "#382c55", "#ceb6ac", "#dcc6b1", "#475569"],
            labels={"Cumulative Value": "Growth (Base 100)", "date": "Date"}
        )
        fig_bench.update_layout(
            hovermode="x unified",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
            height=400
        )
        st.plotly_chart(fig_bench, use_container_width=True)

        st.markdown("##### 📝 Key Insights & Observations")
        col_in1, col_in2 = st.columns(2)
        with col_in1:
            st.info("""
            **📈 Volatility vs. Returns**
            - Small Cap funds outperform on absolute return but carry extreme downside risk (Maximum Drawdowns of ~25%).
            - Gilt and Liquid funds offer defensive risk-adjusted profiles with Sharpe ratios > 1.5, serving as excellent portfolio stabilizers.
            """)
        with col_in2:
            st.info("""
            **📊 Index Tracking**
            - Beta values for large cap schemes stay highly correlated to Nifty 100 (close to 0.9 - 1.0).
            - Active small/mid cap funds exhibit wider tracking errors and higher alpha, showing the active management advantage.
            """)

    with tab_nav:
        st.markdown("""
        | Page | What you'll find |
        |------|-----------------|
        | 🏠 **Overview** | AUM distribution, category breakdown, risk grade heatmap, fund house rankings |
        | 🔍 **Fund Deep Dive** | NAV chart, return comparison, Sharpe ranking, expense ratio analysis |
        | 👥 **Investor Analysis** | SIP trend, cohort behaviour, city-tier breakdown, gender/age distribution |
        | ⚠️ **Risk Analytics** | VaR/CVaR, rolling Sharpe, HHI concentration, max drawdown comparison |
        """)

    with tab_dl:
        st.markdown("You can download the core processed data files below for offline analysis:")
        d1, d2, d3, d4 = st.columns(4)

        db_path = ROOT / "data" / "bluestock_mf.db"
        if db_path.exists():
            with open(db_path, "rb") as f:
                d1.download_button("Download SQLite Database (.db)", f, file_name="bluestock_mf.db", mime="application/octet-stream", use_container_width=True)

        fm_path = DATA / "01_fund_master.csv"
        if fm_path.exists():
            with open(fm_path, "rb") as f:
                d2.download_button("Download Fund Master (.csv)", f, file_name="01_fund_master.csv", mime="text/csv", use_container_width=True)

        sp_path = DATA / "07_scheme_performance.csv"
        if sp_path.exists():
            with open(sp_path, "rb") as f:
                d3.download_button("Download Scheme Performance (.csv)", f, file_name="07_scheme_performance.csv", mime="text/csv", use_container_width=True)

        raw_path = ROOT / "data" / "raw_dataset.zip"
        if raw_path.exists():
            with open(raw_path, "rb") as f:
                d4.download_button("Download Raw Dataset (.zip)", f, file_name="raw_dataset.zip", mime="application/zip", use_container_width=True)

    with tab_nb:
        st.markdown("### 📓 Jupyter Notebooks")
        st.markdown("Download the fully executed analytical notebooks (with embedded plots and insights).")
        
        n1, n2, n3, n4, n5 = st.columns(5)
        
        nb_eda = ROOT / "notebooks" / "mutual_fund_eda.ipynb"
        if nb_eda.exists():
            with open(nb_eda, "rb") as f:
                n1.download_button("Mutual Fund EDA", f, file_name="mutual_fund_eda.ipynb", mime="application/json", use_container_width=True)
                
        nb_perf = ROOT / "notebooks" / "Performance_Analytics.ipynb"
        if nb_perf.exists():
            with open(nb_perf, "rb") as f:
                n2.download_button("Performance Analytics", f, file_name="Performance_Analytics.ipynb", mime="application/json", use_container_width=True)

        nb_adv = ROOT / "notebooks" / "Advanced_Analytics.ipynb"
        if nb_adv.exists():
            with open(nb_adv, "rb") as f:
                n3.download_button("Advanced Analytics", f, file_name="Advanced_Analytics.ipynb", mime="application/json", use_container_width=True)

        nb_mc = ROOT / "notebooks" / "Monte_Carlo.ipynb"
        if nb_mc.exists():
            with open(nb_mc, "rb") as f:
                n4.download_button("Monte Carlo Simulation", f, file_name="Monte_Carlo.ipynb", mime="application/json", use_container_width=True)

        nb_mw = ROOT / "notebooks" / "Markowitz.ipynb"
        if nb_mw.exists():
            with open(nb_mw, "rb") as f:
                n5.download_button("Markowitz Optimization", f, file_name="Markowitz.ipynb", mime="application/json", use_container_width=True)
else:
    st.warning("Please run the ETL pipeline first to generate the processed CSV files.")
