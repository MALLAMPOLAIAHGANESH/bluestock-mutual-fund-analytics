"""
dashboard/app.py
================
Bluestock MF Capstone — V2 Dashboard (Custom Palette & Layout)
"""
import streamlit as st
import os
from pathlib import Path

st.set_page_config(
    page_title="Bluestock MF Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Apply Custom CSS ──
def load_css():
    from pathlib import Path
    import streamlit as st
    css_path = Path(__file__).resolve().parent.parent / 'style.css' if 'pages' in str(Path(__file__).resolve()) else Path(__file__).resolve().parent / 'style.css'
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
load_css()


# ── Sidebar branding
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

# ── Home content
st.title("📈 Bluestock Mutual Fund Analytics")
st.markdown("### Welcome to the Interactive Analytics Dashboard")

# KPI metrics at the top
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Schemes",   "40")
col2.metric("NAV Data Points", "46,000")
col3.metric("Investors",       "5,000")
col4.metric("Transactions",    "32,778")

st.divider()

# A clean tab layout to separate navigation from downloads
tab_nav, tab_dl, tab_nb = st.tabs(["Navigation Guide", "Download Project Data", "Jupyter Notebooks"])

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
    root_dir = Path(__file__).resolve().parent.parent
    d1, d2, d3, d4 = st.columns(4)

    db_path = root_dir / "data" / "bluestock_mf.db"
    if db_path.exists():
        with open(db_path, "rb") as f:
            d1.download_button("Download SQLite Database (.db)", f, file_name="bluestock_mf.db", mime="application/octet-stream", use_container_width=True)

    fm_path = root_dir / "data" / "processed" / "01_fund_master.csv"
    if fm_path.exists():
        with open(fm_path, "rb") as f:
            d2.download_button("Download Fund Master (.csv)", f, file_name="01_fund_master.csv", mime="text/csv", use_container_width=True)

    sp_path = root_dir / "data" / "processed" / "07_scheme_performance.csv"
    if sp_path.exists():
        with open(sp_path, "rb") as f:
            d3.download_button("Download Scheme Performance (.csv)", f, file_name="07_scheme_performance.csv", mime="text/csv", use_container_width=True)

    raw_path = root_dir / "data" / "raw_dataset.zip"
    if raw_path.exists():
        with open(raw_path, "rb") as f:
            d4.download_button("Download Raw Dataset (.zip)", f, file_name="raw_dataset.zip", mime="application/zip", use_container_width=True)

with tab_nb:
    st.markdown("### 📓 Jupyter Notebooks")
    st.markdown("Download the fully executed analytical notebooks (with embedded plots and insights).")
    
    n1, n2, n3, n4, n5 = st.columns(5)
    
    nb_eda = root_dir / "notebooks" / "mutual_fund_eda.csv"
    nb_eda = root_dir / "notebooks" / "mutual_fund_eda.ipynb"
    if nb_eda.exists():
        with open(nb_eda, "rb") as f:
            n1.download_button("Mutual Fund EDA", f, file_name="mutual_fund_eda.ipynb", mime="application/json", use_container_width=True)
            
    nb_perf = root_dir / "notebooks" / "Performance_Analytics.ipynb"
    if nb_perf.exists():
        with open(nb_perf, "rb") as f:
            n2.download_button("Performance Analytics", f, file_name="Performance_Analytics.ipynb", mime="application/json", use_container_width=True)

    nb_adv = root_dir / "notebooks" / "Advanced_Analytics.ipynb"
    if nb_adv.exists():
        with open(nb_adv, "rb") as f:
            n3.download_button("Advanced Analytics", f, file_name="Advanced_Analytics.ipynb", mime="application/json", use_container_width=True)

    nb_mc = root_dir / "notebooks" / "Monte_Carlo.ipynb"
    if nb_mc.exists():
        with open(nb_mc, "rb") as f:
            n4.download_button("Monte Carlo Simulation", f, file_name="Monte_Carlo.ipynb", mime="application/json", use_container_width=True)

    nb_mw = root_dir / "notebooks" / "Markowitz.ipynb"
    if nb_mw.exists():
        with open(nb_mw, "rb") as f:
            n5.download_button("Markowitz Optimization", f, file_name="Markowitz.ipynb", mime="application/json", use_container_width=True)
