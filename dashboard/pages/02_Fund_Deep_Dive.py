"""Page 2 — Fund Deep Dive"""
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Fund Deep Dive | Bluestock MF", layout="wide", page_icon="🔍")

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
    fm   = pd.read_csv(DATA / "01_fund_master.csv")
    return nav, perf, fm

nav, perf, fm = load()
merged = perf.merge(fm[["amfi_code", "fund_manager", "benchmark"]], on="amfi_code", how="left")

# ── Sidebar slicers
with st.sidebar:
    st.header("🔧 Filters")
    risk_grades = ["All"] + sorted(perf["risk_grade"].dropna().unique().tolist())
    sel_risk = st.selectbox("Risk Grade", risk_grades)
    categories = ["All"] + sorted(perf["category"].unique().tolist())
    sel_cat  = st.selectbox("Category", categories)

filt = merged.copy()
if sel_risk != "All": filt = filt[filt["risk_grade"] == sel_risk]
if sel_cat  != "All": filt = filt[filt["category"]   == sel_cat]
fund_list = filt["scheme_name"].tolist()

st.title("🔍 Fund Deep Dive")
tab_viz, tab_comp = st.tabs(["📈 Visual Analysis", "📊 Fund Comparison Table"])

with tab_viz:
    with st.expander("Filter specific fund for NAV view", expanded=True):
        sel_fund = st.selectbox("Select Fund", fund_list if fund_list else ["No funds"])

    if sel_fund and sel_fund != "No funds":
        fund_row = merged[merged["scheme_name"] == sel_fund].iloc[0]
        code     = fund_row["amfi_code"]
        nav_sub  = nav[nav["amfi_code"] == code].sort_values("date")

        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Sharpe Ratio", f"{fund_row.get('sharpe_ratio', 0):.2f}")
        col_b.metric("3Y Return %",  f"{fund_row.get('return_3yr_pct', 0):.1f}%")
        col_c.metric("Max Drawdown", f"{fund_row.get('max_drawdown_pct', 0):.1f}%")
        col_d.metric("AUM (₹ Cr)",   f"{fund_row.get('aum_crore', 0):,.0f}")

        fig_nav = go.Figure()
        fig_nav.add_trace(go.Scatter(
            x=nav_sub["date"], y=nav_sub["nav"],
            mode="lines", name="NAV",
            line=dict(color="#382c55", width=2),
            fill="tozeroy", fillcolor="rgba(100, 130, 160, 0.15)"
        ))
        fig_nav.update_layout(
            title=f"NAV History — {sel_fund}",
            xaxis_title="Date", yaxis_title="NAV (₹)",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=380
        )
        st.plotly_chart(fig_nav, use_container_width=True)

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        top = merged.sort_values("sharpe_ratio", ascending=False).head(15)
        fig_sh = px.bar(top, x="sharpe_ratio", y="scheme_name",
                        orientation="h", color="sharpe_ratio",
                        title="Top 15 Funds by Sharpe Ratio",
                        labels={"sharpe_ratio": "Sharpe Ratio", "scheme_name": "Fund"},
                        color_continuous_scale=["#dcc6b1", "#dea11a", "#742a10", "#382c55"])
        fig_sh.update_layout(height=450, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_sh, use_container_width=True)

    with col2:
        fig_sc = px.scatter(
            merged, x="std_dev_ann_pct", y="return_3yr_pct",
            color="category", size="aum_crore",
            hover_name="scheme_name",
            title="Risk-Return Scatter (3Y)",
            color_discrete_sequence=PALETTE,
            labels={"std_dev_ann_pct": "Std Dev % (Annualised)", "return_3yr_pct": "3Y Return %"},
        )
        fig_sc.update_layout(height=450, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_sc, use_container_width=True)

with tab_comp:
    st.subheader("Fund Comparison Table")
    disp_cols = ["scheme_name", "category", "risk_grade", "return_1yr_pct", "return_3yr_pct", 
                 "return_5yr_pct", "sharpe_ratio", "alpha", "beta", "aum_crore", "expense_ratio_pct"]
    disp_cols = [c for c in disp_cols if c in merged.columns]
    
    st.dataframe(
        merged[disp_cols].sort_values("sharpe_ratio", ascending=False).reset_index(drop=True),
        use_container_width=True, height=600,
        column_config={
            "sharpe_ratio": st.column_config.NumberColumn("Sharpe Ratio", format="%.2f"),
            "aum_crore": st.column_config.NumberColumn("AUM (Cr)", format="₹ %.0f"),
            "return_3yr_pct": st.column_config.ProgressColumn("3Y Return %", format="%.1f%%", min_value=0, max_value=40)
        }
    )
