"""Page 1 — Fund Overview"""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Overview | Bluestock MF", layout="wide", page_icon="🏠")

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
    fm   = pd.read_csv(DATA / "01_fund_master.csv")
    perf = pd.read_csv(DATA / "07_scheme_performance.csv")
    aum  = pd.read_csv(DATA / "03_aum_by_fund_house.csv")
    sip  = pd.read_csv(DATA / "04_monthly_sip_inflows.csv", parse_dates=["month"])
    return fm, perf, aum, sip

fm, perf, aum, sip = load()

# ── Sidebar slicers
with st.sidebar:
    st.header("🔧 Filters")
    fund_houses = ["All"] + sorted(fm["fund_house"].unique().tolist())
    sel_fh = st.selectbox("Fund House", fund_houses)
    categories = ["All"] + sorted(fm["category"].unique().tolist())
    sel_cat = st.selectbox("Category", categories)
    risk_grades = ["All"] + sorted(perf["risk_grade"].dropna().unique().tolist())
    sel_risk = st.selectbox("Risk Grade", risk_grades)

# Apply filters
filt = perf.copy()
if sel_fh   != "All": filt = filt[filt["fund_house"] == sel_fh]
if sel_cat  != "All": filt = filt[filt["category"]   == sel_cat]
if sel_risk != "All": filt = filt[filt["risk_grade"]  == sel_risk]

st.title("🏠 Fund Overview")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Schemes (filtered)", len(filt))
k2.metric("Avg AUM (₹ Cr)", f"{filt['aum_crore'].mean():,.0f}" if "aum_crore" in filt else "N/A")
k3.metric("Avg Sharpe", f"{filt['sharpe_ratio'].mean():.2f}" if "sharpe_ratio" in filt else "N/A")
k4.metric("Avg 3Y Return %", f"{filt['return_3yr_pct'].mean():.1f}%" if "return_3yr_pct" in filt else "N/A")
k5.metric("Avg Expense %", f"{filt['expense_ratio_pct'].mean():.2f}%" if "expense_ratio_pct" in filt else "N/A")
st.divider()

# Layout Tabs
tab_charts, tab_data = st.tabs(["📊 Visual Summary", "📝 Raw Data"])

with tab_charts:
    col1, col2 = st.columns([1.4, 1])

    with col1:
        # AUM by Fund House
        aum_latest = aum.sort_values("date", ascending=False).drop_duplicates("fund_house") if "date" in aum.columns else aum.drop_duplicates("fund_house")
        fig_aum = px.bar(
            aum_latest.sort_values("aum_crore", ascending=True),
            x="aum_crore", y="fund_house", orientation="h",
            title="AUM by Fund House (Latest Month, ₹ Crore)",
            color="aum_crore", color_continuous_scale=["#dcc6b1", "#dea11a", "#742a10", "#382c55"],
            labels={"aum_crore": "AUM (₹ Crore)", "fund_house": "Fund House"},
        )
        fig_aum.update_layout(showlegend=False, height=380, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_aum, use_container_width=True)

    with col2:
        # Category Donut Chart
        cat_counts = filt["category"].value_counts().reset_index()
        cat_counts.columns = ["category", "count"]
        fig_pie = px.pie(cat_counts, names="category", values="count", hole=0.45,
                         title="Scheme Category Distribution",
                         color_discrete_sequence=PALETTE)
        fig_pie.update_layout(height=380, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_pie, use_container_width=True)

    col3, col4 = st.columns([1.2, 1])
    with col3:
        rg = filt.groupby(["category", "risk_grade"]).size().reset_index(name="count")
        fig_tree = px.treemap(rg, path=["category", "risk_grade"], values="count",
                              title="Risk Grade by Category",
                              color="count", color_continuous_scale=["#ceb6ac", "#6482a0", "#382c55"])
        fig_tree.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_tree, use_container_width=True)

    with col4:
        fig_exp = px.box(filt, x="category", y="expense_ratio_pct",
                         title="Expense Ratio (%) by Category",
                         color="category", color_discrete_sequence=PALETTE,
                         labels={"expense_ratio_pct": "Expense Ratio %", "category": "Category"})
        fig_exp.update_layout(showlegend=False, height=360, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_exp, use_container_width=True)

    # SIP trend
    if "inflow_crore" in sip.columns:
        fig_sip = px.area(sip, x="month", y="inflow_crore",
                          title="Monthly SIP Inflows (₹ Crore) — Industry Wide",
                          labels={"inflow_crore": "SIP Inflow (₹ Cr)", "month": "Month"})
        fig_sip.update_traces(fillcolor="rgba(100, 130, 160, 0.2)", line_color="#dea11a")
        fig_sip.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=280)
        st.plotly_chart(fig_sip, use_container_width=True)

with tab_data:
    st.subheader("Fund Master Dataset")
    st.dataframe(fm, use_container_width=True)
