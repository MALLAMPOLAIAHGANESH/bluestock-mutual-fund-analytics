"""Page 4 — Risk Analytics"""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Risk Analytics | Bluestock MF", layout="wide", page_icon="⚠️")

# ── Apply Custom CSS ──
def load_css():
    from pathlib import Path
    import streamlit as st
    css_path = Path(__file__).resolve().parent.parent / 'style.css' if 'pages' in str(Path(__file__).resolve()) else Path(__file__).resolve().parent / 'style.css'
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
load_css()


ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data" / "processed"
PALETTE = ["#dea11a", "#dcc6b1", "#742a10", "#6482a0", "#ceb6ac", "#382c55"]

@st.cache_data
def load():
    nav  = pd.read_csv(DATA / "02_nav_history.csv", parse_dates=["date"])
    perf = pd.read_csv(DATA / "07_scheme_performance.csv")
    port = pd.read_csv(DATA / "09_portfolio_holdings.csv")
    var_path = DATA / "var_cvar_report.csv"
    var_df = pd.read_csv(var_path) if var_path.exists() else pd.DataFrame()
    return nav, perf, port, var_df

nav, perf, port, var_df = load()
nav = nav.sort_values(["amfi_code", "date"])
nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()

with st.expander("ℹ️ How to Interpret Risk Metrics", expanded=False):
    st.markdown("""
    - **VaR 95% (Value at Risk):** The 5th percentile of daily returns. There is a 95% confidence that the fund will not lose more than this percentage on any given day.
    - **CVaR 95% (Conditional VaR):** The expected daily loss, assuming the VaR threshold is breached.
    - **HHI (Herfindahl-Hirschman Index):** Measures portfolio concentration. A score > 0.15 indicates high concentration in a few stocks.
    - **Rolling Sharpe Ratio:** The consistency of risk-adjusted returns over time. A Sharpe > 1 is generally considered good.
    """)

with st.sidebar:
    st.header("🔧 Filters")
    risk_grades = ["All"] + sorted(perf["risk_grade"].dropna().unique().tolist())
    sel_risk = st.selectbox("Risk Grade", risk_grades)
    categories = ["All"] + sorted(perf["category"].unique().tolist())
    sel_cat  = st.selectbox("Category", categories)

filt_perf = perf.copy()
if sel_risk != "All": filt_perf = filt_perf[filt_perf["risk_grade"] == sel_risk]
if sel_cat  != "All": filt_perf = filt_perf[filt_perf["category"]   == sel_cat]
codes_to_show = set(filt_perf["amfi_code"].tolist())

st.title("⚠️ Risk Analytics")

if not var_df.empty and "risk_grade" in var_df.columns:
    vf = var_df[var_df["amfi_code"].isin(codes_to_show)] if codes_to_show else var_df
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Worst Daily VaR 95%",  f"{vf['var_95_pct'].min():.2f}%")
    k2.metric("Avg VaR 95%",          f"{vf['var_95_pct'].mean():.2f}%")
    k3.metric("Avg CVaR 95%",         f"{vf['cvar_95_pct'].mean():.2f}%")
    k4.metric("Avg Annualised Vol %", f"{vf['vol_ann_pct'].mean():.1f}%")
    st.divider()

col1, col2 = st.columns(2)

with col1:
    if not var_df.empty:
        vf2 = var_df.copy()
        if sel_risk != "All" and "risk_grade" in vf2.columns:
            vf2 = vf2[vf2["risk_grade"] == sel_risk]
        vf2 = vf2.sort_values("var_95_pct").head(20)
        fig_var = px.bar(vf2, x="var_95_pct", y="scheme_name", orientation="h",
                         title="Historical VaR 95% — Worst Funds (Daily %)",
                         color="cvar_95_pct", color_continuous_scale=["#382c55", "#742a10", "#dea11a"],
                         labels={"var_95_pct": "VaR 95% (%)", "scheme_name": "Fund"},
                         hover_data=["cvar_95_pct", "vol_ann_pct"])
        fig_var.update_layout(height=450, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_var, use_container_width=True)

with col2:
    KEY_FUNDS = {
        119551: "SBI Bluechip",
        100033: "HDFC Midcap",
        118634: "Nippon Small Cap",
        120841: "Kotak Bluechip",
        119092: "Axis Bluechip",
    }
    fig_rs = go.Figure()
    for (code, label), color in zip(KEY_FUNDS.items(), PALETTE[:5]):
        grp = nav[nav["amfi_code"] == code].set_index("date")["daily_return"].dropna()
        if len(grp) < 90: continue
        rs = (grp.rolling(90).mean() / grp.rolling(90).std()) * np.sqrt(252)
        fig_rs.add_trace(go.Scatter(x=rs.dropna().index, y=rs.dropna().values, name=label,
                                    line=dict(color=color, width=1.8)))
    fig_rs.add_hline(y=1, line_dash="dot", line_color="#888888")
    fig_rs.add_hline(y=0, line_dash="dash", line_color="#555555")
    fig_rs.update_layout(
        title="Rolling 90-Day Sharpe Ratio (Annualised) — 5 Key Funds",
        xaxis_title="Date", yaxis_title="Sharpe Ratio",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=450
    )
    st.plotly_chart(fig_rs, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    hhi = port.groupby("amfi_code")["weight_pct"].apply(lambda w: float(((w / 100) ** 2).sum())).reset_index()
    hhi.columns = ["amfi_code", "HHI"]
    hhi = hhi.merge(perf[["amfi_code", "scheme_name", "category"]], on="amfi_code", how="left")
    if codes_to_show: hhi = hhi[hhi["amfi_code"].isin(codes_to_show)]
    fig_hhi = px.bar(
        hhi.sort_values("HHI", ascending=False), x="scheme_name", y="HHI",
        title="Portfolio Concentration — HHI Score (higher = more concentrated)",
        color="HHI", color_continuous_scale=["#dcc6b1", "#742a10"]
    )
    fig_hhi.add_hline(y=0.15, line_dash="dot", line_color="#6482a0", annotation_text="HHI 0.15 = moderate")
    fig_hhi.update_layout(xaxis_tickangle=-45, height=400, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_hhi, use_container_width=True)

with col4:
    if "max_drawdown_pct" in filt_perf.columns:
        dd = filt_perf.sort_values("max_drawdown_pct").head(20)
        fig_dd = px.bar(dd, x="max_drawdown_pct", y="scheme_name", orientation="h",
                        title="Maximum Drawdown % — Worst 20 Funds",
                        color="max_drawdown_pct", color_continuous_scale=["#742a10", "#dea11a"],
                        labels={"max_drawdown_pct": "Max Drawdown %", "scheme_name": "Fund"})
        fig_dd.update_layout(height=400, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_dd, use_container_width=True)
