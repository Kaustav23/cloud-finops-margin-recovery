"""
Cloud FinOps & Unit Margin Recovery Engine (`app.py`)
=====================================================
Flagship Interactive Streamlit Dashboard for Zombie Infrastructure & EBITDA Erosion Analytics.
Designed for both technical VPs of Engineering and non-technical CFOs, recruiters, and stakeholders.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from finops_engine import build_remediation_export_df, evaluate_cloud_fleet
from generate_empirical_data import generate_telemetry_dataset

# ---------------------------------------------------------------------------
# 1. PAGE CONFIG & EXECUTIVE DARK/SLATE STYLING
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Cloud FinOps & Unit Margin Recovery Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    /* Clean Executive Dark/Slate Theme */
    .stApp {
        background-color: #0B0F19;
        color: #F8FAFC;
    }
    .main-header {
        background: linear-gradient(135deg, #111827 0%, #1E293B 100%);
        border: 1px solid #334155;
        border-left: 5px solid #10B981;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 18px;
    }
    .main-title {
        font-size: 1.75rem;
        font-weight: 800;
        color: #F8FAFC;
        margin: 0 0 6px 0;
        letter-spacing: -0.02em;
    }
    .main-subtitle {
        font-size: 0.96rem;
        color: #94A3B8;
        margin: 0;
        line-height: 1.5;
    }
    .kpi-card {
        background: #111827;
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 16px 18px;
        height: 100%;
        min-height: 182px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }
    .kpi-label {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.65rem;
        font-weight: 800;
        color: #F8FAFC;
        line-height: 1.15;
        margin-bottom: 8px;
    }
    .kpi-badge {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.76rem;
        font-weight: 600;
        margin-bottom: 10px;
        width: fit-content;
    }
    .kpi-plain-english {
        font-size: 0.79rem;
        color: #CBD5E1;
        line-height: 1.4;
        border-top: 1px solid #1E293B;
        padding-top: 8px;
    }
    .verdict-box {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.10) 0%, rgba(17, 24, 39, 0.95) 100%);
        border: 1px solid #10B981;
        border-radius: 12px;
        padding: 18px 22px;
        margin-top: 12px;
        margin-bottom: 16px;
    }
    .bucket-card {
        background: #111827;
        border-radius: 10px;
        padding: 16px 18px;
        border: 1px solid #1E293B;
        height: 100%;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Semantic Palette Constants
COLOR_ZOMBIE = "#EF4444"     # Crimson/Coral: Zombie Waste / Immediate Termination
COLOR_RIGHTSIZE = "#F59E0B"  # Amber: Over-Provisioned / Right-Size Downgrade
COLOR_COMMIT = "#10B981"     # Emerald: Recovered EBITDA / RI & Savings Plan Lock-In
COLOR_HEALTHY = "#3B82F6"    # Slate/Blue: Healthy / Optimized Baseline
COLOR_BUFFER = "#6366F1"     # Indigo: Engineering Safety Headroom Buffer

ACTION_COLOR_MAP = {
    "Immediate Termination": COLOR_ZOMBIE,
    "Right-Size Downgrade": COLOR_RIGHTSIZE,
    "Reserved Instance / Savings Plan Lock-In": COLOR_COMMIT,
    "Healthy / Optimized Baseline": COLOR_HEALTHY,
}


# ---------------------------------------------------------------------------
# 2. DATA LOADING (AUTO-LOAD OR FALLBACK GENERATE)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_telemetry_data() -> pd.DataFrame:
    csv_path = Path(__file__).resolve().parent / "cloud_telemetry_logs.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    df_gen = generate_telemetry_dataset(n_records=3200, seed=42)
    df_gen.to_csv(csv_path, index=False)
    return df_gen


raw_df = load_telemetry_data()


# ---------------------------------------------------------------------------
# 3. INTERACTIVE SIDEBAR ("EXECUTIVE SIMULATION & SAFETY CONTROLS")
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Executive Simulation & Safety Controls")
    st.caption(
        "Stress-test SaaS unit margin impact, engineering P95 headroom guardrails, "
        "and AWS Savings Plan lock-in horizons in real time."
    )

    st.markdown("### 1. Company SaaS Financial Context")
    company_arr_m = st.slider(
        "Annual Recurring Revenue (ARR $M)",
        min_value=10.0,
        max_value=100.0,
        value=25.0,
        step=1.0,
        format="$%.0fM",
        help="Company top-line Annual Recurring Revenue used to translate cloud COGS savings into Gross Margin basis points (bps).",
    )
    company_arr_usd = company_arr_m * 1_000_000.0

    baseline_gm_pct = st.slider(
        "Baseline Gross Margin (%) Before FinOps",
        min_value=45.0,
        max_value=85.0,
        value=68.0,
        step=0.5,
        format="%.1f%%",
        help="Current SaaS Gross Margin percentage before cloud waste remediation.",
    )

    st.markdown("### 2. Engineering Safety Guardrails")
    headroom_buffer_pct = st.slider(
        "P95 Peak Headroom Buffer (%)",
        min_value=15,
        max_value=50,
        value=30,
        step=5,
        format="%d%%",
        help="Guarantees that even during peak traffic spikes, downsized servers retain at least X% spare capacity so production never crashes.",
    )
    st.info(
        f"**Safety Guardrail Active:** Guarantees that even during 95th-percentile traffic spikes, "
        f"downsized servers retain at least **{headroom_buffer_pct}% spare capacity** "
        f"(and P99 peak stays ≤92%) so production never crashes."
    )

    commitment_term = st.radio(
        "Commitment Lock-In Strategy",
        options=[
            "1-Year Savings Plan (Conservative)",
            "3-Year Savings Plan (Aggressive)",
        ],
        index=0,
        help="Applies documented AWS Compute/Instance Savings Plan discount rates (32% for 1-Yr; 54% for 3-Yr) to steady-state On-Demand workloads (Uptime >= 95%, CV <= 0.35).",
    )

    st.markdown("### 3. Infrastructure Scope Filters")
    all_envs = ["Production", "AI/ML GPU Cluster", "Staging", "Development"]
    selected_envs = st.multiselect(
        "Environment",
        options=all_envs,
        default=all_envs,
    )

    all_services = ["Compute EC2/VM", "Managed Database RDS", "Block Storage EBS"]
    selected_services = st.multiselect(
        "Cloud Service Type",
        options=all_services,
        default=all_services,
    )

    all_bus = ["Core Platform", "AI Inference", "Data Engineering", "Internal Tools"]
    selected_bus = st.multiselect(
        "Business Unit",
        options=all_bus,
        default=all_bus,
    )

# Apply user filters safely
filtered_raw = raw_df[
    (raw_df["environment"].isin(selected_envs))
    & (raw_df["service_type"].isin(selected_services))
    & (raw_df["business_unit"].isin(selected_bus))
].copy()

evaluated_df, kpis = evaluate_cloud_fleet(
    df=filtered_raw,
    headroom_buffer_pct=float(headroom_buffer_pct),
    commitment_term=commitment_term,
    company_arr_usd=company_arr_usd,
    baseline_gross_margin_pct=baseline_gm_pct,
)


# ---------------------------------------------------------------------------
# 4. HEADER & EMPIRICAL BENCHMARKS DRAWER
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="main-header">
        <div class="main-title">⚡ Cloud FinOps & Unit Margin Recovery Engine</div>
        <div class="main-subtitle">
            <strong>Zombie Infrastructure &amp; EBITDA Erosion Analytics</strong> — Empirical P95/P99 workload right-sizing,
            zero-risk zombie decommissioning, and commitment rate optimization grounded in
            <a href="https://data.finops.org/" target="_blank" style="color:#10B981;text-decoration:none;">FinOps Foundation</a>,
            <a href="https://www.flexera.com/about-us/press-center/new-flexera-report-finds-84-percent-of-organizations-struggle-to-manage-cloud-spend" target="_blank" style="color:#10B981;text-decoration:none;">Flexera State of the Cloud</a>,
            and <a href="https://www.microsoft.com/en-us/research/wp-content/uploads/2017/10/Resource-Central-SOSP17.pdf" target="_blank" style="color:#10B981;text-decoration:none;">Microsoft Research (Resource Central, SOSP '17)</a>.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("📚 Research Methodology & Empirical Benchmarks (Click to Audit Data Grounding & Citations)", expanded=False):
    st.markdown(
        """
        Every threshold, utilization curve, and discount rate in this engine is anchored in peer-reviewed systems research and authoritative FinOps industry benchmarks:
        - **Industry Cloud Waste Benchmark (27%–32%):** Grounded in the [Flexera State of the Cloud Report](https://www.flexera.com/about-us/press-center/new-flexera-report-finds-84-percent-of-organizations-struggle-to-manage-cloud-spend) and [Cloud Waste Synthesis (2020–2026)](https://ideatives.com/briefs/cloud-cost/), which document **27%–32% wasted cloud spend** annually (29% median in 2026), alongside the [HashiCorp State of Cloud Strategy Survey](https://www.hashicorp.com/en/blog/new-survey-shows-broad-cloud-waste-hashicorp-terraform-can-help) (94% of enterprises report avoidable spend: 66% idle/underused resources, 59% over-provisioned resources).
        - **Heavy-Tailed Telemetry & P95 Right-Sizing Headroom:** Grounded in [Cortez et al. (2017), *Resource Central: Understanding and Predicting Workloads for Improved Resource Management in Large Cloud Platforms* (Microsoft Research / ACM SOSP '17)](https://www.microsoft.com/en-us/research/wp-content/uploads/2017/10/Resource-Central-SOSP17.pdf), [Reiss et al. (2012), *Heterogeneity and Dynamicity of Clouds at Scale: Google Trace Analysis* (ACM SoCC '12)](https://www.pdl.cmu.edu/PDL-FTP/CloudComputing/googletrace-socc2012.pdf), and the [AWS Well-Architected Framework — Cost Optimization Pillar](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html). Rather than using dangerous average CPU cutoffs that crash spiky workloads, right-sizing evaluates $\\max(\\text{P95}_{\\text{CPU}}, \\text{P95}_{\\text{RAM}}) \\times (1 + \\text{Headroom Buffer})$ and enforces a strict $\\text{P99} \\le 92\\%$ post-downgrade ceiling.
        - **Effective Savings Rate (ESR) & Commitment Optimization:** Grounded in the [FinOps Foundation Rate Optimization Framework](https://www.finops.org/framework/capabilities/rate-optimization/) and [FinOps ESR Playbook](https://www.finout.io/blog/effective-savings-rate-measure-commitment-savings) ($\\text{ESR} = \\text{Net Savings} / \\text{On-Demand Equivalent Spend}$), using documented [AWS EC2 On-Demand Pricing](https://aws.amazon.com/ec2/pricing/on-demand/), [AWS Compute Savings Plans Pricing](https://aws.amazon.com/savingsplans/compute-pricing/) (32% 1-Yr / 54% 3-Yr discounts), [Amazon RDS Pricing](https://aws.amazon.com/rds/custom/pricing/), and [Amazon EBS Pricing](https://aws.amazon.com/ebs/pricing/) ($0.08/GB-mo `gp3`, $0.125/GB-mo `io2`).
        """
    )

if evaluated_df.empty:
    st.warning("No cloud telemetry records match the current sidebar filter selection. Please select at least one Environment, Cloud Service, and Business Unit.")
    st.stop()


# ---------------------------------------------------------------------------
# 5. TOP EXECUTIVE KPI STRIP (5 CRYSTAL-CLEAR CARDS WITH PLAIN-ENGLISH SUBTITLES)
# ---------------------------------------------------------------------------
def fmt_currency(val: float) -> str:
    if abs(val) >= 1_000_000:
        return f"${val / 1_000_000:,.2f}M ($" + f"{val:,.0f})"
    return f"${val:,.0f}"


def fmt_short_currency(val: float) -> str:
    if abs(val) >= 1_000_000:
        return f"${val / 1_000_000:,.2f}M"
    return f"${val:,.0f}"


waste_delta_vs_bench = kpis["identified_waste_rate_pct"] - kpis["industry_waste_midpoint_pct"]
waste_badge_text = (
    f"{kpis['identified_waste_rate_pct']:.1f}% Waste ({waste_delta_vs_bench:+.1f}% vs 29.0% Flexera Benchmark)"
)

kpi_cols = st.columns(5)

# Card 1: Annualized Cloud Spend (Run-Rate)
with kpi_cols[0]:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-top: 3px solid {COLOR_HEALTHY};">
            <div>
                <div class="kpi-label">1. Annualized Cloud Spend</div>
                <div class="kpi-value">{fmt_short_currency(kpis['annual_billed_spend_usd'])}</div>
                <div class="kpi-badge" style="background:rgba(59,130,246,0.15);color:#60A5FA;">
                    {kpis['cloud_pct_of_arr_before']:.1f}% of ARR (${kpis['monthly_billed_spend_usd']:,.0f}/mo)
                </div>
            </div>
            <div class="kpi-plain-english">
                What the company is currently on track to spend on cloud servers, storage, and AI GPUs this year.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Card 2: Identified Cloud Waste Rate (% & $)
with kpi_cols[1]:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-top: 3px solid {COLOR_ZOMBIE};">
            <div>
                <div class="kpi-label">2. Identified Cloud Waste Rate</div>
                <div class="kpi-value" style="color:#F87171;">{kpis['identified_waste_rate_pct']:.1f}% ({fmt_short_currency(kpis['total_annual_savings_usd'])})</div>
                <div class="kpi-badge" style="background:rgba(239,68,68,0.15);color:#FCA5A5;">
                    Industry Avg: 27%–32% (Flexera 2026: 29.0%)
                </div>
            </div>
            <div class="kpi-plain-english">
                Money currently being burned on idle servers, unattached hard drives, and oversized databases.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Card 3: Projected 12-Month Cash Savings
with kpi_cols[2]:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-top: 3px solid {COLOR_COMMIT};">
            <div>
                <div class="kpi-label">3. Projected 12-Mo Cash Savings</div>
                <div class="kpi-value" style="color:#34D399;">${kpis['total_annual_savings_usd']:,.0f}</div>
                <div class="kpi-badge" style="background:rgba(16,185,129,0.15);color:#6EE7B7;">
                    ${kpis['total_monthly_savings_usd']:,.0f}/mo Across {kpis['actionable_resources']:,} Assets
                </div>
            </div>
            <div class="kpi-plain-english">
                Hard cash saved over the next 12 months without slowing down product performance.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Card 4: Gross Margin & EBITDA Recovery
with kpi_cols[3]:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-top: 3px solid {COLOR_COMMIT};">
            <div>
                <div class="kpi-label">4. Gross Margin &amp; EBITDA Lift</div>
                <div class="kpi-value" style="color:#34D399;">+{kpis['gross_margin_expansion_pct_pts']:.1f}% (+{kpis['gross_margin_expansion_bps']:.0f} bps)</div>
                <div class="kpi-badge" style="background:rgba(16,185,129,0.15);color:#6EE7B7;">
                    Margin: {kpis['baseline_gross_margin_pct']:.1f}% &rarr; {kpis['new_gross_margin_pct']:.1f}%
                </div>
            </div>
            <div class="kpi-plain-english">
                How much healthier the company's core profit margin becomes once cloud waste is eliminated.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Card 5: Effective Savings Rate (ESR)
with kpi_cols[4]:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-top: 3px solid {COLOR_RIGHTSIZE};">
            <div>
                <div class="kpi-label">5. Effective Savings Rate (ESR)</div>
                <div class="kpi-value" style="color:#FBBF24;">{kpis['optimized_esr_pct']:.1f}%</div>
                <div class="kpi-badge" style="background:rgba(245,158,11,0.15);color:#FCD34D;">
                    +{kpis['esr_expansion_pct']:.1f}% vs {kpis['baseline_esr_pct']:.1f}% Baseline ESR
                </div>
            </div>
            <div class="kpi-plain-english">
                Overall discount and efficiency score achieved across all cloud infrastructure.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 6. FOUR STRUCTURED DASHBOARD TABS
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📊 Tab 1: Executive Verdict & Margin Impact (CFO View)",
        "🛡️ Tab 2: Engineering Safety & Utilization Diagnostics (VP Eng View)",
        "🎯 Tab 3: Prioritized Remediation Matrix (Action Plan)",
        "📖 Tab 4: Research Methodology, Formulas & Audit Trail",
    ]
)

# ===========================================================================
# TAB 1: EXECUTIVE VERDICT & MARGIN IMPACT (THE CFO VIEW)
# ===========================================================================
with tab1:
    # Plain-English Executive Summary Box
    st.markdown(
        f"""
        <div class="verdict-box">
            <h4 style="margin:0 0 8px 0; color:#34D399; font-size:1.08rem;">
                💡 Plain-English Executive Verdict (Current Filtered Scope: {kpis['total_resources']:,} Cloud Resources)
            </h4>
            <p style="margin:0; font-size:0.95rem; color:#F1F5F9; line-height:1.55;">
                Out of <strong>${kpis['annual_billed_spend_usd']:,.0f}</strong> in annualized cloud spend,
                <strong>${kpis['total_annual_savings_usd']:,.0f} ({kpis['identified_waste_rate_pct']:.1f}%)</strong> is recoverable waste —
                lifting company Gross Margin from <strong>{kpis['baseline_gross_margin_pct']:.1f}% to {kpis['new_gross_margin_pct']:.1f}%
                (+{kpis['gross_margin_expansion_pct_pts']:.1f}% / +{kpis['gross_margin_expansion_bps']:.0f} bps)</strong> and adding
                <strong>${kpis['total_annual_savings_usd']:,.0f}</strong> directly to 12-month run-rate EBITDA.
                The <strong>#1 largest source of recoverable waste</strong> in this view is
                <strong>{kpis['top_hotspot_env']} &mdash; {kpis['top_hotspot_svc']} (${kpis['top_hotspot_usd']:,.0f}/yr)</strong>.
                <strong>Fastest Zero-Risk Action This Week:</strong> Immediately snapshot and decommission the
                <strong>{kpis['zombie_termination_count']:,} verified Zombie/Orphaned assets</strong> to lock in
                <strong>${kpis['zombie_termination_savings_usd']:,.0f}/yr</strong> with zero production impact, while Finance locks in
                <strong>{kpis['commitment_term']}</strong> across <strong>{kpis['commitment_lockin_count']:,} steady-state servers</strong>
                for an immediate <strong>${kpis['commitment_lockin_savings_usd']:,.0f}/yr</strong> billing reduction.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_wf, col_donut = st.columns([1.35, 1.0])

    with col_wf:
        st.markdown("#### 12-Month Cloud Spend Reduction & EBITDA Recovery Waterfall")
        st.caption(
            "**How to read this chart (5-Second Takeaway):** Starting from the current annual cloud bill on the left (Blue), "
            "each middle bar shows hard dollar savings unlocked by our 3 FinOps levers, arriving at the lean Post-FinOps Cloud Spend on the right."
        )

        wf_fig = go.Figure(
            go.Waterfall(
                name="Cloud Spend Bridge",
                orientation="v",
                measure=["absolute", "relative", "relative", "relative", "total"],
                x=[
                    "Current Annual<br>Cloud Spend",
                    "1. Immediate<br>Termination (Zombies)",
                    "2. Right-Size<br>Downgrade (P95 Safe)",
                    "3. RI / Savings Plan<br>Rate Lock-In",
                    "Optimized Annual<br>Cloud Spend",
                ],
                textposition="outside",
                text=[
                    f"${kpis['annual_billed_spend_usd']/1e6:.2f}M",
                    f"-${kpis['zombie_termination_savings_usd']/1e3:,.0f}K",
                    f"-${kpis['rightsizing_savings_usd']/1e3:,.0f}K",
                    f"-${kpis['commitment_lockin_savings_usd']/1e3:,.0f}K",
                    f"${kpis['post_remediation_annual_spend_usd']/1e6:.2f}M",
                ],
                y=[
                    kpis["annual_billed_spend_usd"],
                    -kpis["zombie_termination_savings_usd"],
                    -kpis["rightsizing_savings_usd"],
                    -kpis["commitment_lockin_savings_usd"],
                    kpis["post_remediation_annual_spend_usd"],
                ],
                connector={"line": {"color": "#475569", "width": 1.5, "dash": "dot"}},
                decreasing={"marker": {"color": COLOR_COMMIT}},
                increasing={"marker": {"color": COLOR_ZOMBIE}},
                totals={"marker": {"color": COLOR_HEALTHY}},
            )
        )
        wf_fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(17,24,39,0.6)",
            height=430,
            margin=dict(l=20, r=20, t=35, b=20),
            yaxis=dict(
                title="Annual Cloud Spend ($ USD)",
                tickprefix="$",
                gridcolor="#1E293B",
                zerolinecolor="#334155",
            ),
            xaxis=dict(title=""),
            showlegend=False,
        )
        st.plotly_chart(wf_fig, use_container_width=True)

    with col_donut:
        st.markdown("#### Total Cloud Spend Efficiency Breakdown")
        st.caption(
            "**How to read this chart (5-Second Takeaway):** Splits every dollar of your current cloud bill into productive "
            "work (Blue/Indigo) versus the 3 categories of avoidable waste (Red, Amber, Emerald)."
        )

        slice_labels = [
            "Productive Utilized Spend",
            f"Engineering P95 Safety Buffer (+{headroom_buffer_pct}%)",
            "Zombie Waste (Immediate Termination)",
            "Right-Sizing Excess (Over-Provisioned)",
            "On-Demand Rate Premium (RI/SP Lock-In)",
        ]
        slice_values = [
            kpis["productive_utilized_spend_usd"],
            kpis["engineering_buffer_spend_usd"],
            kpis["zombie_termination_savings_usd"],
            kpis["rightsizing_savings_usd"],
            kpis["commitment_lockin_savings_usd"],
        ]
        slice_colors = [
            COLOR_HEALTHY,
            COLOR_BUFFER,
            COLOR_ZOMBIE,
            COLOR_RIGHTSIZE,
            COLOR_COMMIT,
        ]

        donut_fig = go.Figure(
            data=[
                go.Pie(
                    labels=slice_labels,
                    values=slice_values,
                    hole=0.56,
                    marker=dict(colors=slice_colors, line=dict(color="#0B0F19", width=2)),
                    textinfo="percent",
                    hovertemplate="<b>%{label}</b><br>Annual Spend: $%{value:,.0f}<br>Share of Bill: %{percent}<extra></extra>",
                )
            ]
        )
        donut_fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=430,
            margin=dict(l=10, r=10, t=25, b=10),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.28,
                xanchor="center",
                x=0.5,
                font=dict(size=11),
            ),
            annotations=[
                dict(
                    text=(
                        f"<b>{kpis['identified_waste_rate_pct']:.1f}%</b><br>"
                        f"<span style='font-size:11px;color:#94A3B8;'>Recoverable<br>Waste</span>"
                    ),
                    x=0.5,
                    y=0.5,
                    font_size=18,
                    showarrow=False,
                    font_color="#F8FAFC",
                )
            ],
        )
        st.plotly_chart(donut_fig, use_container_width=True)

    # Bottom Row of Tab 1: Gross Margin Expansion Bridge Table for CFO Audit
    st.markdown("#### CFO Unit Economics & Gross Margin Expansion Summary")
    st.caption(
        "Direct translation of cloud infrastructure remediation into SaaS Gross Profit and EBITDA expansion "
        "(grounded in [FinOps Foundation Unit Economics Framework](https://www.finops.org/framework/capabilities/rate-optimization/))."
    )
    cfo_summary_df = pd.DataFrame(
        [
            {
                "Financial Metric": "Company Annual Recurring Revenue (ARR)",
                "Baseline (Pre-FinOps)": f"${kpis['company_arr_usd']:,.0f}",
                "Post-FinOps Remediation": f"${kpis['company_arr_usd']:,.0f}",
                "Net Financial Impact": "Unchanged Top-Line Revenue",
            },
            {
                "Financial Metric": "Annualized Cloud Infrastructure COGS",
                "Baseline (Pre-FinOps)": f"${kpis['annual_billed_spend_usd']:,.0f} ({kpis['cloud_pct_of_arr_before']:.1f}% of ARR)",
                "Post-FinOps Remediation": f"${kpis['post_remediation_annual_spend_usd']:,.0f} ({kpis['cloud_pct_of_arr_after']:.1f}% of ARR)",
                "Net Financial Impact": f"-${kpis['total_annual_savings_usd']:,.0f}/yr COGS Reduction (-{kpis['identified_waste_rate_pct']:.1f}%)",
            },
            {
                "Financial Metric": "Annual Gross Profit & 12-Mo EBITDA Contribution",
                "Baseline (Pre-FinOps)": f"${kpis['baseline_gross_profit_usd']:,.0f}",
                "Post-FinOps Remediation": f"${kpis['new_gross_profit_usd']:,.0f}",
                "Net Financial Impact": f"+${kpis['total_annual_savings_usd']:,.0f}/yr Direct EBITDA Cash Recovery",
            },
            {
                "Financial Metric": "SaaS Gross Margin (% and Basis Points)",
                "Baseline (Pre-FinOps)": f"{kpis['baseline_gross_margin_pct']:.1f}%",
                "Post-FinOps Remediation": f"{kpis['new_gross_margin_pct']:.1f}%",
                "Net Financial Impact": f"+{kpis['gross_margin_expansion_pct_pts']:.1f}% (+{kpis['gross_margin_expansion_bps']:.0f} bps Expansion)",
            },
            {
                "Financial Metric": "FinOps Effective Savings Rate (ESR vs. On-Demand Equivalent)",
                "Baseline (Pre-FinOps)": f"{kpis['baseline_esr_pct']:.1f}% (Existing Commitments: ${kpis['existing_commitment_savings_usd']:,.0f})",
                "Post-FinOps Remediation": f"{kpis['optimized_esr_pct']:.1f}% (Total Savings vs ODE: ${kpis['existing_commitment_savings_usd'] + kpis['total_annual_savings_usd']:,.0f})",
                "Net Financial Impact": f"+{kpis['esr_expansion_pct']:.1f}% Efficiency Gain (Coverage: {kpis['commitment_coverage_before_pct']:.1f}% -> {kpis['commitment_coverage_after_pct']:.1f}%)",
            },
        ]
    )
    st.dataframe(cfo_summary_df, use_container_width=True, hide_index=True)


# ===========================================================================
# TAB 2: ENGINEERING SAFETY & UTILIZATION DIAGNOSTICS (THE VP OF ENG VIEW)
# ===========================================================================
with tab2:
    st.markdown("#### Utilization vs. Monthly Cost Quadrant Scatter Plot (Engineering Safety Proof)")
    st.caption(
        "**How to read this chart (5-Second Takeaway):** Each bubble is a cloud cluster (sized by vCPUs/GPUs). "
        "**Red bubbles (`Immediate Termination`) sit strictly in the bottom-left dead zone (<5% peak load)**, proving that "
        "spiky production servers on the right (`>50%` P95 peak) are 100% protected from accidental termination."
    )

    # Calculate dynamic right-sizing P95 cutoff line based on user's headroom slider:
    # Since buffered_p95 <= 48.0% triggers 1-step downgrade, raw P95 cutoff is 48.0 / (1 + buffer/100)
    dynamic_p95_cutoff = 48.0 / (1.0 + float(headroom_buffer_pct) / 100.0)

    scatter_sample = evaluated_df.copy()
    scatter_sample["bubble_size"] = np.maximum(scatter_sample["vcpu_count"], 2)

    quad_fig = px.scatter(
        scatter_sample,
        x="dominant_p95_pct",
        y="monthly_billed_cost_usd",
        color="recommended_action",
        size="bubble_size",
        size_max=22,
        color_discrete_map=ACTION_COLOR_MAP,
        category_orders={
            "recommended_action": [
                "Immediate Termination",
                "Right-Size Downgrade",
                "Reserved Instance / Savings Plan Lock-In",
                "Healthy / Optimized Baseline",
            ]
        },
        hover_name="cluster_id",
        hover_data={
            "environment": True,
            "service_type": True,
            "instance_tier": True,
            "avg_cpu_pct": ":.1f",
            "dominant_p95_pct": ":.1f",
            "dominant_p99_pct": ":.1f",
            "monthly_billed_cost_usd": ":$,.2f",
            "annual_savings_usd": ":$,.2f",
            "target_tier_fix": True,
            "bubble_size": False,
        },
        labels={
            "dominant_p95_pct": "30-Day P95 Peak Utilization (Max of CPU/IOPS & RAM %)",
            "monthly_billed_cost_usd": "Current Monthly Billed Cost ($ USD, Log Scale)",
            "recommended_action": "Executive Remediation Action",
        },
        log_y=True,
    )

    # Add Zombie Cutoff Line (5% P95) and Dynamic Right-Sizing Cutoff Line
    quad_fig.add_vline(
        x=5.0,
        line_width=2,
        line_dash="dash",
        line_color=COLOR_ZOMBIE,
        annotation_text="Zombie Cutoff (<5% P95)",
        annotation_position="top left",
        annotation_font_color=COLOR_ZOMBIE,
    )
    quad_fig.add_vline(
        x=dynamic_p95_cutoff,
        line_width=2,
        line_dash="dot",
        line_color=COLOR_RIGHTSIZE,
        annotation_text=f"Right-Size Threshold ({dynamic_p95_cutoff:.1f}% P95 @ +{headroom_buffer_pct}% Buffer)",
        annotation_position="top right",
        annotation_font_color=COLOR_RIGHTSIZE,
    )

    quad_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.6)",
        height=470,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            title="",
        ),
        xaxis=dict(gridcolor="#1E293B", range=[-2, 100], ticksuffix="%"),
        yaxis=dict(gridcolor="#1E293B", tickprefix="$"),
    )
    st.plotly_chart(quad_fig, use_container_width=True)

    st.info(
        f"🛡️ **Zero False-Positive Spiky Workload Protection (Cortez et al., SOSP '17):** "
        f"In the current view, **{kpis['spiky_protected_count']:,} diurnal/spiky clusters** have low average CPU (<22%) "
        f"that naive average-based tools would falsely flag as idle, but exhibit **P95 bursts ≥50%**. "
        f"Our engine automatically isolates and protects all **{kpis['spiky_protected_count']:,}** spiky clusters from termination or unsafe downsizing."
    )

    col_heat, col_stab = st.columns(2)

    with col_heat:
        st.markdown("#### Environment × Service Type Waste Concentration Heatmap")
        st.caption(
            "**How to read this chart (5-Second Takeaway):** Pinpoints the exact intersection of Environment and Cloud Service "
            "where the most annual dollars are being wasted right now."
        )

        heat_pivot = (
            evaluated_df.pivot_table(
                index="environment",
                columns="service_type",
                values="annual_savings_usd",
                aggfunc="sum",
                fill_value=0.0,
            )
            .reindex(index=[e for e in all_envs if e in selected_envs], fill_value=0.0)
            .reindex(columns=[s for s in all_services if s in selected_services], fill_value=0.0)
        )

        text_matrix = [
            [f"${val:,.0f}" for val in row] for row in heat_pivot.values
        ]

        heat_fig = go.Figure(
            data=go.Heatmap(
                z=heat_pivot.values,
                x=list(heat_pivot.columns),
                y=list(heat_pivot.index),
                text=text_matrix,
                texttemplate="<b>%{text}</b>",
                colorscale=[
                    [0.0, "#111827"],
                    [0.35, "#1E3A8A"],
                    [0.7, "#D97706"],
                    [1.0, "#EF4444"],
                ],
                hovertemplate="Environment: <b>%{y}</b><br>Service: <b>%{x}</b><br>Recoverable Waste: <b>$%{z:,.0f}/yr</b><extra></extra>",
                colorbar=dict(title="Waste ($/yr)", tickprefix="$"),
            )
        )
        heat_fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(17,24,39,0.6)",
            height=390,
            margin=dict(l=20, r=20, t=25, b=20),
            xaxis=dict(title="Cloud Service Tier"),
            yaxis=dict(title="Deployment Environment", autorange="reversed"),
        )
        st.plotly_chart(heat_fig, use_container_width=True)

    with col_stab:
        st.markdown("#### Workload Stability vs. Pricing Model Matrix")
        st.caption(
            "**How to read this chart (5-Second Takeaway):** Steady-state workloads live in the **top-left green zone** "
            "(Uptime ≥95%, Load Variation CV ≤0.35). Any `On-Demand` server in that box is overpaying by 32%–54%."
        )

        compute_rds_df = evaluated_df[
            (evaluated_df["service_type"].isin(["Compute EC2/VM", "Managed Database RDS"]))
            & (evaluated_df["recommended_action"] != "Immediate Termination")
        ].copy()

        stab_fig = px.scatter(
            compute_rds_df,
            x="usage_cv",
            y="uptime_pct_30d",
            color="pricing_model",
            size="annual_billed_cost_usd",
            size_max=18,
            color_discrete_map={
                "On-Demand": COLOR_ZOMBIE,
                "1-Yr Savings Plan": COLOR_HEALTHY,
                "3-Yr Savings Plan": COLOR_COMMIT,
            },
            hover_name="cluster_id",
            hover_data={
                "environment": True,
                "instance_tier": True,
                "recommended_action": True,
                "annual_billed_cost_usd": ":$,.0f",
                "annual_savings_usd": ":$,.0f",
            },
            labels={
                "usage_cv": "30-Day Hourly Load Coefficient of Variation (CV = σ/μ; Lower = More Stable)",
                "uptime_pct_30d": "30-Day Uptime Consistency (%)",
                "pricing_model": "Current Billing Model",
            },
        )
        # Highlight the Steady-State Savings Plan Lock-In Eligibility Box (CV <= 0.35, Uptime >= 95%)
        stab_fig.add_shape(
            type="rect",
            x0=0.0,
            x1=0.35,
            y0=95.0,
            y1=100.5,
            line=dict(color=COLOR_COMMIT, width=2, dash="dash"),
            fillcolor="rgba(16, 185, 129, 0.10)",
        )
        stab_fig.add_annotation(
            x=0.175,
            y=99.6,
            text="Steady-State SP Lock-In Zone (Uptime ≥95%, CV ≤0.35)",
            showarrow=False,
            font=dict(color="#34D399", size=11),
        )
        stab_fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(17,24,39,0.6)",
            height=390,
            margin=dict(l=20, r=20, t=25, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, title=""),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B", ticksuffix="%"),
        )
        st.plotly_chart(stab_fig, use_container_width=True)


# ===========================================================================
# TAB 3: PRIORITIZED REMEDIATION MATRIX (THE ACTIONABLE EXECUTION PLAN)
# ===========================================================================
with tab3:
    st.markdown("#### Executive 3-Bucket Remediation Action Plan")
    st.caption(
        "Every actionable cloud asset is classified into one of three mutually exclusive execution buckets "
        "ordered by implementation speed and engineering risk."
    )

    b_cols = st.columns(3)
    with b_cols[0]:
        st.markdown(
            f"""
            <div class="bucket-card" style="border-left: 4px solid {COLOR_ZOMBIE};">
                <div style="font-size:0.8rem;font-weight:700;color:#FCA5A5;text-transform:uppercase;">
                    Bucket 1 &bull; Execute Today (Zero Risk)
                </div>
                <div style="font-size:1.22rem;font-weight:800;color:#F8FAFC;margin:4px 0;">
                    Immediate Termination
                </div>
                <div style="font-size:1.55rem;font-weight:800;color:#F87171;margin-bottom:6px;">
                    ${kpis['zombie_termination_savings_usd']:,.0f}/yr
                    <span style="font-size:0.85rem;color:#94A3B8;font-weight:500;">
                        ({kpis['zombie_termination_count']:,} Zombie Assets)
                    </span>
                </div>
                <div style="font-size:0.82rem;color:#CBD5E1;line-height:1.45;">
                    Unattached EBS storage volumes with 0 IOPS for &ge;14 days and abandoned non-prod instances
                    with P95 CPU &lt;5% and P95 RAM &lt;10%. Take final archival snapshot and delete immediately.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with b_cols[1]:
        st.markdown(
            f"""
            <div class="bucket-card" style="border-left: 4px solid {COLOR_RIGHTSIZE};">
                <div style="font-size:0.8rem;font-weight:700;color:#FCD34D;text-transform:uppercase;">
                    Bucket 2 &bull; Execute Next Sprint (P95 Buffered)
                </div>
                <div style="font-size:1.22rem;font-weight:800;color:#F8FAFC;margin:4px 0;">
                    Right-Size Downgrade
                </div>
                <div style="font-size:1.55rem;font-weight:800;color:#FBBF24;margin-bottom:6px;">
                    ${kpis['rightsizing_savings_usd']:,.0f}/yr
                    <span style="font-size:0.85rem;color:#94A3B8;font-weight:500;">
                        ({kpis['rightsizing_count']:,} Oversized Assets)
                    </span>
                </div>
                <div style="font-size:0.82rem;color:#CBD5E1;line-height:1.45;">
                    Over-provisioned EC2, GPU, RDS, and EBS tiers where P95 peak load plus your
                    <strong>+{headroom_buffer_pct}% safety headroom buffer</strong> still utilizes &le;48% of capacity
                    (and P99 stays &le;92%).
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with b_cols[2]:
        st.markdown(
            f"""
            <div class="bucket-card" style="border-left: 4px solid {COLOR_COMMIT};">
                <div style="font-size:0.8rem;font-weight:700;color:#6EE7B7;text-transform:uppercase;">
                    Bucket 3 &bull; Finance Action (Zero Code Change)
                </div>
                <div style="font-size:1.22rem;font-weight:800;color:#F8FAFC;margin:4px 0;">
                    RI / Savings Plan Lock-In
                </div>
                <div style="font-size:1.55rem;font-weight:800;color:#34D399;margin-bottom:6px;">
                    ${kpis['commitment_lockin_savings_usd']:,.0f}/yr
                    <span style="font-size:0.85rem;color:#94A3B8;font-weight:500;">
                        ({kpis['commitment_lockin_count']:,} Steady-State Assets)
                    </span>
                </div>
                <div style="font-size:0.82rem;color:#CBD5E1;line-height:1.45;">
                    Well-sized steady-state workloads (&ge;95% uptime, load CV &le;0.35) currently paying expensive
                    On-Demand rates. Lock in <strong>{kpis['commitment_term']} ({kpis['commitment_discount_pct']:.0f}% discount)</strong>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Interactive Table Filter & 1-Click CSV Export
    export_df = build_remediation_export_df(evaluated_df)

    filter_col1, filter_col2, dl_col = st.columns([1.4, 1.4, 1.0])
    with filter_col1:
        bucket_filter = st.multiselect(
            "Filter Table by Remediation Action Bucket",
            options=[
                "Immediate Termination",
                "Right-Size Downgrade",
                "Reserved Instance / Savings Plan Lock-In",
            ],
            default=[
                "Immediate Termination",
                "Right-Size Downgrade",
                "Reserved Instance / Savings Plan Lock-In",
            ],
        )
    with filter_col2:
        search_query = st.text_input(
            "Search by Cluster ID, Instance Tier, or Justification",
            value="",
            placeholder="e.g., g5.4xlarge, db.r6i, unattached, CL-PROD...",
        )

    filtered_table = export_df[export_df["Recommended Action"].isin(bucket_filter)].copy()
    if search_query.strip():
        q = search_query.strip().lower()
        mask = (
            filtered_table["Cluster ID"].str.lower().str.contains(q, na=False)
            | filtered_table["Service & Current Tier"].str.lower().str.contains(q, na=False)
            | filtered_table["Plain-English Justification"].str.lower().str.contains(q, na=False)
        )
        filtered_table = filtered_table[mask].copy()

    with dl_col:
        st.markdown("<div style='height: 26px;'></div>", unsafe_allow_html=True)
        csv_bytes = filtered_table.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"📥 Download Executive Remediation Plan.csv ({len(filtered_table):,} rows)",
            data=csv_bytes,
            file_name="Download Executive Remediation Plan.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown(
        f"**Showing {len(filtered_table):,} prioritized remediation actions** "
        f"(Ranked by **12-Month Cash Savings Descending** — Total Selected Savings: "
        f"**${filtered_table['12-Month Cash Savings ($)'].sum():,.2f}/yr**)"
    )

    st.dataframe(
        filtered_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Current Annual Cost ($)": st.column_config.NumberColumn(
                "Current Annual Cost", format="$%,.2f"
            ),
            "12-Month Cash Savings ($)": st.column_config.NumberColumn(
                "12-Month Cash Savings", format="$%,.2f"
            ),
        },
        height=460,
    )


# ===========================================================================
# TAB 4: RESEARCH METHODOLOGY, FORMULAS & AUDIT TRAIL
# ===========================================================================
with tab4:
    st.markdown("### 🔬 Quantitative Methodology, Mathematical Formulas & Empirical Citations")
    st.caption(
        "Complete audit trail for technical interviewers, FinOps architects, and financial controllers."
    )

    m_col1, m_col2 = st.columns(2)

    with m_col1:
        st.markdown("#### 1. P95/P99 Safety-Buffered Right-Sizing Formula")
        st.markdown(
            "Per [Cortez et al. (Microsoft Research / ACM SOSP '17)](https://www.microsoft.com/en-us/research/wp-content/uploads/2017/10/Resource-Central-SOSP17.pdf) "
            "and the [AWS Well-Architected Cost Optimization Pillar](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html), "
            "sizing instances on average CPU causes severe throttling during diurnal traffic bursts. "
            "Instead, we compute the **Buffered P95 Dominant Utilization** across CPU/IOPS and Memory:"
        )
        st.latex(
            r"U_{\text{buffered}} = \max\left(P_{95}^{\text{CPU}},\, P_{95}^{\text{RAM}}\right) \times \left(1 + \frac{B_{\text{headroom}}}{100}\right)"
        )
        st.markdown(
            "A 1-step instance family downgrade (which halves vCPU/RAM capacity, $C_{\\text{ratio}} = 0.50$) is executed **if and only if** both conditions hold:"
        )
        st.latex(
            r"U_{\text{buffered}} \le 48.0\% \quad \text{and} \quad 2 \times \max\left(P_{99}^{\text{CPU}},\, P_{99}^{\text{RAM}}\right) \le 92.0\%"
        )

        st.markdown("#### 2. Effective Savings Rate (ESR) — FinOps Foundation")
        st.markdown(
            "Per the [FinOps Foundation Rate Optimization Capability](https://www.finops.org/framework/capabilities/rate-optimization/) "
            "and [FinOps ESR Playbook](https://www.finout.io/blog/effective-savings-rate-measure-commitment-savings), "
            "Effective Savings Rate measures net cost efficiency relative to **On-Demand Equivalent (ODE)** spend:"
        )
        st.latex(
            r"\text{ESR}_{\text{optimized}} = \frac{(\text{Spend}_{\text{ODE}} - \text{Spend}_{\text{Billed}}) + \text{Savings}_{\text{Term}} + \text{Savings}_{\text{RightSize}} + \text{Savings}_{\text{SP}}}{\text{Spend}_{\text{ODE}}}"
        )

    with m_col2:
        st.markdown("#### 3. SaaS Gross Margin & 12-Month EBITDA Recovery")
        st.markdown(
            "Cloud infrastructure hosting is a direct **Cost of Goods Sold (COGS)** line item for SaaS and AI platforms. "
            "Every dollar of eliminated cloud waste flows dollar-for-dollar into Gross Profit and 12-Month Run-Rate EBITDA:"
        )
        st.latex(
            r"\Delta \text{Gross Margin (\%)} = \left(\frac{\text{Savings}_{\text{12M Total}}}{\text{Company ARR}}\right) \times 100"
        )
        st.latex(
            r"\Delta \text{Gross Margin (bps)} = \Delta \text{Gross Margin (\%)} \times 100"
        )
        st.latex(
            r"\text{Gross Margin}_{\text{Post-FinOps}} = \text{Gross Margin}_{\text{Baseline}} + \Delta \text{Gross Margin (\%)}"
        )

        st.markdown("#### 4. Zombie vs. Spiky Production Isolation Rule")
        st.markdown(
            "To guarantee **zero false-positive termination alerts**, a resource is classified into `Immediate Termination` "
            "strictly when:"
        )
        st.latex(
            r"\text{Zombie}_{\text{EBS}} \iff \neg\text{Attached} \;\land\; \text{IOPS}_{\text{avg}} = 0 \;\land\; D_{\text{idle}} \ge 14\text{ days}"
        )
        st.latex(
            r"\text{Zombie}_{\text{Compute/RDS}} \iff P_{95}^{\text{CPU}} < 5\% \;\land\; P_{95}^{\text{RAM}} < 10\% \;\land\; \text{Net}_{\text{IO}} < 0.5\text{ MB/s} \;\land\; D_{\text{idle}} \ge 14\text{ days}"
        )

    st.markdown("#### 5. Authoritative References & Empirical Grounding Table")
    citations_table = pd.DataFrame(
        [
            {
                "Domain / Parameter": "Industry Cloud Waste Rate (27%–32%; 29% in 2026)",
                "Authoritative Source": "Flexera State of the Cloud Report (2025/2026) & Ideatives Synthesis",
                "Empirical Parameter Used in Engine": "Fleet waste calibrated to ~29.8% across Idle Zombies, Over-Provisioning, and On-Demand Rate Premium.",
                "Reference URL": "https://ideatives.com/briefs/cloud-cost/",
            },
            {
                "Domain / Parameter": "Idle vs. Over-Provisioned Waste Drivers",
                "Authoritative Source": "HashiCorp State of Cloud Strategy Survey (Forrester Consulting)",
                "Empirical Parameter Used in Engine": "94% of enterprises report avoidable spend: 66% from idle/underused assets, 59% from over-provisioning.",
                "Reference URL": "https://www.hashicorp.com/en/blog/new-survey-shows-broad-cloud-waste-hashicorp-terraform-can-help",
            },
            {
                "Domain / Parameter": "Effective Savings Rate (ESR) & Commitment Coverage",
                "Authoritative Source": "FinOps Foundation State of FinOps 2026 & Rate Optimization Framework",
                "Empirical Parameter Used in Engine": "ESR = Total Net Savings / On-Demand Equivalent Spend; tracks 1-Yr (32%) and 3-Yr (54%) Savings Plans.",
                "Reference URL": "https://www.finops.org/framework/capabilities/rate-optimization/",
            },
            {
                "Domain / Parameter": "Heavy-Tailed VM Telemetry & Diurnal Spikes",
                "Authoritative Source": "Cortez et al. (2017), Microsoft Research 'Resource Central' (ACM SOSP '17)",
                "Empirical Parameter Used in Engine": "Log-normal CPU/RAM utilization, P95/P99 tail buffers, and CV <= 0.35 stability threshold for commitments.",
                "Reference URL": "https://www.microsoft.com/en-us/research/wp-content/uploads/2017/10/Resource-Central-SOSP17.pdf",
            },
            {
                "Domain / Parameter": "Cluster Heterogeneity & CPU-Memory Skewness",
                "Authoritative Source": "Reiss et al. (2012), 'Google Trace Analysis' (ACM SoCC '12 Test of Time Award)",
                "Empirical Parameter Used in Engine": "Decoupled CPU and RAM peak distributions across General Purpose (m6i), Memory (r6i), and GPU (g5) tiers.",
                "Reference URL": "https://www.pdl.cmu.edu/PDL-FTP/CloudComputing/googletrace-socc2012.pdf",
            },
            {
                "Domain / Parameter": "AWS EC2, RDS & EBS Public Pricing & Savings Plans",
                "Authoritative Source": "AWS Official On-Demand, Savings Plans, RDS & EBS Pricing (us-east-1)",
                "Empirical Parameter Used in Engine": "Exact hourly rates for m6i/r6i/g5 EC2, db.m6i/db.r6i RDS, and $0.08/GB-mo gp3 / $0.125/GB-mo io2 EBS.",
                "Reference URL": "https://aws.amazon.com/ec2/pricing/on-demand/",
            },
        ]
    )
    st.dataframe(
        citations_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Reference URL": st.column_config.LinkColumn("Verified Source Link"),
        },
    )