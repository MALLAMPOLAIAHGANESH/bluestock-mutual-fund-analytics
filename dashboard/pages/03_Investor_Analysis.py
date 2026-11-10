"""Page 3 — Investor Analysis"""
from pathlib import Path
import pandas as pd
# pyrefly: ignore [missing-import]
import plotly.express as px
# pyrefly: ignore [missing-import]
import streamlit as st

st.set_page_config(page_title="Investor Analysis | Bluestock MF", layout="wide", page_icon="👥")

# ── Apply Custom CSS ──
def load_css():
    from pathlib import Path
    # pyrefly: ignore [missing-import]
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
    txn  = pd.read_csv(DATA / "08_investor_transactions.csv", parse_dates=["transaction_date"])
    perf = pd.read_csv(DATA / "07_scheme_performance.csv")
    sip  = pd.read_csv(DATA / "04_monthly_sip_inflows.csv", parse_dates=["month"])
    return txn, perf, sip

txn, perf, sip = load()
txn = txn.merge(perf[["amfi_code", "scheme_name", "category"]], on="amfi_code", how="left")

with st.sidebar:
    st.header("🔧 Filters")
    txn_types = ["All"] + sorted(txn["transaction_type"].dropna().unique().tolist())
    sel_type  = st.selectbox("Transaction Type", txn_types)
    states = ["All"] + sorted(txn["state"].dropna().unique().tolist()) if "state" in txn.columns else ["All"]
    sel_state = st.selectbox("State", states)

filt = txn.copy()
if sel_type  != "All": filt = filt[filt["transaction_type"] == sel_type]
if sel_state != "All" and "state" in filt: filt = filt[filt["state"] == sel_state]

st.title("👥 Investor Analysis")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Investors (filtered)", f"{filt['investor_id'].nunique():,}")
k2.metric("Transactions",         f"{len(filt):,}")
k3.metric("Total Invested (₹ Cr)", f"{filt['amount_inr'].sum()/1e7:,.1f}")
k4.metric("Avg SIP Amount (₹)",   f"{filt[filt['transaction_type']=='SIP']['amount_inr'].mean():,.0f}" if "SIP" in filt["transaction_type"].values else "N/A")
st.divider()

t1, t2, t3 = st.tabs(["📈 SIP Trends", "🗺️ Demographics", "📊 Cohort Insights"])

with t1:
    col1, col2 = st.columns(2)
    with col1:
        if "inflow_crore" in sip.columns:
            fig_sip = px.line(sip, x="month", y="inflow_crore",
                              title="Industry SIP Inflows (₹ Crore) — Monthly Trend",
                              markers=True, labels={"inflow_crore": "SIP Inflow (₹ Cr)", "month": "Month"})
            fig_sip.update_traces(line_color="#dea11a")
            fig_sip.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=320)
            st.plotly_chart(fig_sip, use_container_width=True)

    with col2:
        if "scheme_name" in filt.columns:
            top_funds = filt.groupby("scheme_name")["amount_inr"].sum().nlargest(10).reset_index()
            top_funds.columns = ["Fund", "Total (₹)"]
            fig_tf = px.bar(top_funds, x="Total (₹)", y="Fund", orientation="h",
                            title="Top 10 Funds by Transaction Volume",
                            color="Total (₹)", color_continuous_scale=["#dcc6b1", "#6482a0", "#dea11a"])
            fig_tf.update_layout(showlegend=False, height=320, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_tf, use_container_width=True)

with t2:
    col3, col4 = st.columns(2)
    with col3:
        if "city_tier" in filt.columns:
            # Change pie to stacked bar for readability
            tier = filt.groupby("city_tier")["amount_inr"].sum().reset_index()
            tier.columns = ["City Tier", "Total Invested (₹)"]
            fig_tier = px.bar(tier, x="City Tier", y="Total Invested (₹)",
                              title="Investment by City Tier", color="City Tier",
                              color_discrete_sequence=PALETTE)
            fig_tier.update_layout(height=320, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_tier, use_container_width=True)

    with col4:
        if "gender" in filt.columns:
            gen_cnt = filt["gender"].value_counts().reset_index()
            gen_cnt.columns = ["Gender", "Count"]
            fig_gen = px.pie(gen_cnt, names="Gender", values="Count", hole=0.4,
                             title="Investor Gender Distribution",
                             color_discrete_sequence=["#6482a0", "#dea11a", "#382c55"])
            fig_gen.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_gen, use_container_width=True)

with t3:
    if "age_group" in filt.columns:
        first_yr = filt.groupby("investor_id")["transaction_date"].min().dt.year.rename("cohort")
        filt2 = filt.merge(first_yr.reset_index(), on="investor_id")
        cohort = filt2[filt2["transaction_type"] == "SIP"].groupby("cohort")["amount_inr"].mean().reset_index()
        cohort.columns = ["Cohort Year", "Avg SIP (₹)"]
        fig_coh = px.bar(cohort, x="Cohort Year", y="Avg SIP (₹)",
                         title="Avg SIP Amount by Investor Cohort (First-Transaction Year)",
                         color="Avg SIP (₹)", color_continuous_scale=["#ceb6ac", "#742a10", "#dea11a"])
        fig_coh.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=380)
        st.plotly_chart(fig_coh, use_container_width=True)
