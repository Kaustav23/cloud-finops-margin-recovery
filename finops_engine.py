"""
Cloud FinOps & Unit Margin Recovery Quantitative Engine (`finops_engine.py`)
============================================================================
Pure, decoupled quantitative analytics and optimization engine (zero Streamlit UI code).
Implements:
1. Zombie Asset Detection Logic (separating true Orphaned/Zombie assets from Spiky Production).
2. P95/P99 Safety-Buffered Right-Sizing Algorithm (Cortez et al., 2017; AWS Well-Architected).
3. Commitment Optimization (1-Year vs. 3-Year Savings Plan Lock-In & Effective Savings Rate).
4. Unit Margin & EBITDA Recovery Calculator (SaaS Gross Margin bps/percentage point expansion).
5. Prioritized Remediation Matrix Engine (3 mutually exclusive executive action buckets).
"""

from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd


# Lookup table for next-lower tier downgrade within each AWS hardware family
DOWNGRADE_TIER_MAP = {
    # Compute EC2 M6i
    ("m6i", 4): ("m6i.2xlarge", 0.50),
    ("m6i", 3): ("m6i.xlarge", 0.50),
    ("m6i", 2): ("m6i.large", 0.50),
    # Compute EC2 R6i
    ("r6i", 4): ("r6i.2xlarge", 0.50),
    ("r6i", 3): ("r6i.xlarge", 0.50),
    ("r6i", 2): ("r6i.large", 0.50),
    # AI/ML GPU G5
    ("g5", 4): ("g5.4xlarge", round(1.624 / 5.672, 4)),
    ("g5", 3): ("g5.2xlarge", round(1.212 / 1.624, 4)),
    ("g5", 2): ("g5.xlarge", round(1.006 / 1.212, 4)),
    # Managed Database RDS M6i
    ("db.m6i", 4): ("db.m6i.2xlarge", 0.50),
    ("db.m6i", 3): ("db.m6i.xlarge", 0.50),
    ("db.m6i", 2): ("db.m6i.large", 0.50),
    # Managed Database RDS R6i
    ("db.r6i", 4): ("db.r6i.2xlarge", 0.50),
    ("db.r6i", 3): ("db.r6i.xlarge", 0.50),
    ("db.r6i", 2): ("db.r6i.large", 0.50),
    # Block Storage EBS gp3 & io2 (downgrade oversized capacity or migrate over-provisioned io2 -> gp3)
    ("ebs.gp3", 4): ("ebs.gp3.2TB", 0.50),
    ("ebs.gp3", 3): ("ebs.gp3.1TB", 0.50),
    ("ebs.gp3", 2): ("ebs.gp3.500GB", 0.50),
    ("ebs.io2", 4): ("ebs.gp3.2TB (io2->gp3)", round(0.08 / 0.125, 4)),
    ("ebs.io2", 3): ("ebs.gp3.1TB (io2->gp3)", round(0.08 / 0.125, 4)),
}

TWO_STEP_DOWNGRADE_MAP = {
    ("m6i", 4): ("m6i.xlarge", 0.25),
    ("m6i", 3): ("m6i.large", 0.25),
    ("r6i", 4): ("r6i.xlarge", 0.25),
    ("r6i", 3): ("r6i.large", 0.25),
    ("db.m6i", 4): ("db.m6i.xlarge", 0.25),
    ("db.m6i", 3): ("db.m6i.large", 0.25),
    ("db.r6i", 4): ("db.r6i.xlarge", 0.25),
    ("db.r6i", 3): ("db.r6i.large", 0.25),
    ("ebs.gp3", 4): ("ebs.gp3.1TB", 0.25),
    ("ebs.gp3", 3): ("ebs.gp3.500GB", 0.25),
}

COMMITMENT_DISCOUNTS = {
    "1-Year Savings Plan (Conservative)": {
        "discount_rate": 0.32,
        "label": "1-Yr Savings Plan (32% Off On-Demand)",
        "short_label": "1-Yr SP Lock-In (-32%)",
    },
    "3-Year Savings Plan (Aggressive)": {
        "discount_rate": 0.54,
        "label": "3-Yr Savings Plan (54% Off On-Demand)",
        "short_label": "3-Yr SP Lock-In (-54%)",
    },
}


def evaluate_cloud_fleet(
    df: pd.DataFrame,
    headroom_buffer_pct: float = 30.0,
    commitment_term: str = "1-Year Savings Plan (Conservative)",
    company_arr_usd: float = 25_000_000.0,
    baseline_gross_margin_pct: float = 68.0,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Executes the full FinOps diagnostic, P95 safety-buffered right-sizing, commitment optimization,
    and SaaS Unit Margin / EBITDA recovery model across the filtered cloud telemetry dataset.

    Parameters
    ----------
    df : pd.DataFrame
        Input telemetry dataframe from `cloud_telemetry_logs.csv`.
    headroom_buffer_pct : float
        Engineering safety headroom buffer added above P95 peak utilization (e.g., 30.0 for +30%).
    commitment_term : str
        Either "1-Year Savings Plan (Conservative)" or "3-Year Savings Plan (Aggressive)".
    company_arr_usd : float
        Annual Recurring Revenue (ARR) in USD for unit economics / Gross Margin translation.
    baseline_gross_margin_pct : float
        Baseline company Gross Margin percentage prior to FinOps remediation.

    Returns
    -------
    Tuple[pd.DataFrame, Dict[str, Any]]
        - Enriched dataframe with remediation classifications, target tiers, savings, and justifications.
        - Dictionary of executive KPIs, waterfall components, spend efficiency slices, and benchmarks.
    """
    if df.empty:
        empty_kpis = _build_empty_kpis(company_arr_usd, baseline_gross_margin_pct, headroom_buffer_pct, commitment_term)
        return df.copy(), empty_kpis

    work = df.copy()
    headroom_mult = 1.0 + (float(headroom_buffer_pct) / 100.0)
    sp_config = COMMITMENT_DISCOUNTS.get(
        commitment_term, COMMITMENT_DISCOUNTS["1-Year Savings Plan (Conservative)"]
    )
    sp_discount = sp_config["discount_rate"]

    # 1. Dominant Peak Utilization (P95 and P99 across CPU/IOPS and RAM)
    work["dominant_p95_pct"] = np.maximum(work["p95_cpu_pct"], work["p95_ram_pct"])
    work["dominant_p99_pct"] = np.maximum(work["p99_cpu_pct"], work["p99_ram_pct"])
    work["buffered_p95_pct"] = np.round(work["dominant_p95_pct"] * headroom_mult, 2)

    # 2. Vectorized / Row-level classification into mutually exclusive Executive Action Buckets
    actions = []
    target_tiers = []
    risk_levels = []
    annual_savings = []
    target_annual_costs = []
    justifications = []
    spiky_protected_flags = []

    for row in work.itertuples(index=False):
        cur_cost = float(row.annual_billed_cost_usd)
        p95_dom = float(row.dominant_p95_pct)
        p99_dom = float(row.dominant_p99_pct)
        buffered_p95 = float(row.buffered_p95_pct)
        fam = str(row.instance_family)
        rank = int(row.tier_rank)

        # Check Spiky Production protection status (low mean <22%, high P95 >=50% or diurnal ratio >= 3.0)
        is_spiky_prod = (
            float(row.avg_cpu_pct) < 22.0
            and (float(row.p95_cpu_pct) >= 50.0 or float(row.diurnal_peak_ratio) >= 3.0)
        )
        spiky_protected_flags.append(is_spiky_prod)

        # BUCKET 1: Immediate Termination (Zero-Risk Zombie / Orphaned Infrastructure)
        is_storage_zombie = (
            row.service_type == "Block Storage EBS"
            and (not bool(row.is_attached))
            and int(row.zero_activity_days) >= 14
            and float(row.iops_avg) == 0.0
        )
        is_compute_zombie = (
            row.service_type != "Block Storage EBS"
            and float(row.p95_cpu_pct) < 5.0
            and float(row.p95_ram_pct) < 10.0
            and float(row.network_io_mbps) < 0.5
            and int(row.zero_activity_days) >= 14
        )

        if is_storage_zombie or is_compute_zombie:
            actions.append("Immediate Termination")
            target_tiers.append("Decommission / Delete")
            risk_levels.append("Zero Risk (Verified Zombie)")
            annual_savings.append(round(cur_cost, 2))
            target_annual_costs.append(0.0)
            if is_storage_zombie:
                justifications.append(
                    f"Unattached {int(row.storage_gb)}GB {row.instance_tier} volume with 0.0 IOPS for "
                    f"{int(row.zero_activity_days)} consecutive days — safe to snapshot and delete immediately."
                )
            else:
                justifications.append(
                    f"Abandoned {row.environment} {row.instance_tier} with P95 CPU {row.p95_cpu_pct:.1f}%, "
                    f"P95 RAM {row.p95_ram_pct:.1f}%, and near-zero network I/O for {int(row.zero_activity_days)} days."
                )
            continue

        # BUCKET 2: P95/P99 Safety-Buffered Right-Sizing Downgrade
        # Check if 2-step or 1-step downgrade is safe under the user-selected P95 Headroom Buffer
        # and P99 saturation ceiling (<=92% post-downgrade peak capacity)
        can_two_step = (
            (fam, rank) in TWO_STEP_DOWNGRADE_MAP
            and buffered_p95 <= 24.0
            and (p99_dom * 4.0) <= 92.0
            and not is_spiky_prod
        )
        can_one_step = (
            (fam, rank) in DOWNGRADE_TIER_MAP
            and buffered_p95 <= 48.0
            and (p99_dom * 2.0) <= 92.0
            and not is_spiky_prod
        )

        if can_two_step:
            new_tier, cost_ratio = TWO_STEP_DOWNGRADE_MAP[(fam, rank)]
            new_cost = round(cur_cost * cost_ratio, 2)
            saved = round(cur_cost - new_cost, 2)
            actions.append("Right-Size Downgrade")
            target_tiers.append(new_tier)
            risk_levels.append(f"Low Risk (P95 + {headroom_buffer_pct:.0f}% Buffer)")
            annual_savings.append(saved)
            target_annual_costs.append(new_cost)
            justifications.append(
                f"P95 peak is {p95_dom:.1f}% ({buffered_p95:.1f}% with +{headroom_buffer_pct:.0f}% safety buffer); "
                f"2-step downgrade {row.instance_tier} -> {new_tier} cuts cost by {(1.0 - cost_ratio)*100:.0f}% safely."
            )
            continue

        if can_one_step:
            new_tier, cost_ratio = DOWNGRADE_TIER_MAP[(fam, rank)]
            new_cost = round(cur_cost * cost_ratio, 2)
            saved = round(cur_cost - new_cost, 2)
            actions.append("Right-Size Downgrade")
            target_tiers.append(new_tier)
            risk_levels.append(f"Low Risk (P95 + {headroom_buffer_pct:.0f}% Buffer)")
            annual_savings.append(saved)
            target_annual_costs.append(new_cost)
            justifications.append(
                f"P95 peak is {p95_dom:.1f}% ({buffered_p95:.1f}% with +{headroom_buffer_pct:.0f}% safety buffer); "
                f"1-step downgrade {row.instance_tier} -> {new_tier} cuts cost by {(1.0 - cost_ratio)*100:.0f}% with zero outage risk."
            )
            continue

        # BUCKET 3: Reserved Instance / Savings Plan Lock-In (Steady-State On-Demand Workloads)
        is_steady_on_demand = (
            row.service_type in ["Compute EC2/VM", "Managed Database RDS"]
            and row.pricing_model == "On-Demand"
            and float(row.uptime_pct_30d) >= 95.0
            and float(row.usage_cv) <= 0.35
        )

        if is_steady_on_demand:
            saved = round(cur_cost * sp_discount, 2)
            new_cost = round(cur_cost - saved, 2)
            actions.append("Reserved Instance / Savings Plan Lock-In")
            target_tiers.append(f"{row.instance_tier} ({sp_config['short_label']})")
            risk_levels.append("Zero Engineering Risk (Billing Only)")
            annual_savings.append(saved)
            target_annual_costs.append(new_cost)
            justifications.append(
                f"Steady-state {row.environment} workload ({row.uptime_pct_30d:.1f}% uptime, CV {row.usage_cv:.2f}) "
                f"on expensive On-Demand rate; lock in {sp_config['label']} with zero code/infra change."
            )
            continue

        # BUCKET 4: Healthy / Protected Baseline (Already Optimized or Spiky Production Protected)
        actions.append("Healthy / Optimized Baseline")
        target_tiers.append(f"{row.instance_tier} (Retain Current)")
        if is_spiky_prod:
            risk_levels.append("Protected (Spiky P95 Burst)")
            justifications.append(
                f"Protected Spiky Workload: Avg CPU is {row.avg_cpu_pct:.1f}% but P95 spikes to {row.p95_cpu_pct:.1f}% "
                f"(P99 {row.p99_cpu_pct:.1f}%) — retained at {row.instance_tier} to prevent production throttling."
            )
        else:
            risk_levels.append("Optimal Baseline")
            justifications.append(
                f"Well-sized {row.environment} resource (P95 peak {p95_dom:.1f}%, buffered {buffered_p95:.1f}%) "
                f"operating within target efficiency guardrails on {row.pricing_model}."
            )
        annual_savings.append(0.0)
        target_annual_costs.append(cur_cost)

    work["is_spiky_protected"] = spiky_protected_flags
    work["recommended_action"] = actions
    work["target_tier_fix"] = target_tiers
    work["risk_level"] = risk_levels
    work["annual_savings_usd"] = annual_savings
    work["post_remediation_annual_cost_usd"] = target_annual_costs
    work["monthly_savings_usd"] = np.round(work["annual_savings_usd"] / 12.0, 2)
    work["plain_english_justification"] = justifications

    # 3. Spend Efficiency Decomposition (for Donut/Sunburst & Executive Audit)
    # Break down each active dollar of Current Annual Billed Spend into:
    # - Zombie Waste (Immediate Termination bucket)
    # - Right-Sizing Excess (Right-Size Downgrade savings)
    # - On-Demand Rate Premium (RI / Savings Plan Lock-In savings)
    # - Engineering Safety Buffer (Headroom capacity retained above P95 on active instances)
    # - Productive Utilized Spend (Core utilized capacity driving customer workloads)
    total_billed_annual = float(work["annual_billed_cost_usd"].sum())
    total_od_equiv_annual = float(work["annual_on_demand_cost_usd"].sum())

    term_mask = work["recommended_action"] == "Immediate Termination"
    rightsize_mask = work["recommended_action"] == "Right-Size Downgrade"
    sp_mask = work["recommended_action"] == "Reserved Instance / Savings Plan Lock-In"

    zombie_waste_usd = float(work.loc[term_mask, "annual_savings_usd"].sum())
    rightsize_waste_usd = float(work.loc[rightsize_mask, "annual_savings_usd"].sum())
    ondemand_premium_usd = float(work.loc[sp_mask, "annual_savings_usd"].sum())

    total_savings_usd = zombie_waste_usd + rightsize_waste_usd + ondemand_premium_usd
    post_remediation_spend_usd = max(0.0, total_billed_annual - total_savings_usd)

    # Split post_remediation_spend_usd into Productive Utilized Spend vs. Engineering Safety Headroom Buffer
    safety_share = (headroom_buffer_pct / 100.0) / (1.0 + (headroom_buffer_pct / 100.0))
    engineering_buffer_spend_usd = round(post_remediation_spend_usd * safety_share * 0.65, 2)
    productive_utilized_spend_usd = round(post_remediation_spend_usd - engineering_buffer_spend_usd, 2)

    waste_rate_pct = (total_savings_usd / total_billed_annual * 100.0) if total_billed_annual > 0 else 0.0

    # 4. Effective Savings Rate (ESR) Calculations (FinOps Foundation Framework)
    # Existing commitment savings = On-Demand Equivalent Spend - Current Billed Spend
    existing_commitment_savings_usd = max(0.0, total_od_equiv_annual - total_billed_annual)
    baseline_esr_pct = (
        (existing_commitment_savings_usd / total_od_equiv_annual) * 100.0
        if total_od_equiv_annual > 0
        else 0.0
    )
    # Total Optimized Effective Savings Rate = (Existing Commitment Discount + New FinOps Remediation Savings) / ODE Spend
    optimized_esr_pct = (
        ((existing_commitment_savings_usd + total_savings_usd) / total_od_equiv_annual) * 100.0
        if total_od_equiv_annual > 0
        else 0.0
    )
    esr_expansion_pct = optimized_esr_pct - baseline_esr_pct

    # Commitment Coverage Ratio among eligible steady-state compute/RDS workloads
    eligible_compute_rds = work[
        (work["service_type"].isin(["Compute EC2/VM", "Managed Database RDS"]))
        & (~term_mask)
    ]
    if len(eligible_compute_rds) > 0:
        elig_spend = float(eligible_compute_rds["annual_on_demand_cost_usd"].sum())
        covered_before = float(
            eligible_compute_rds.loc[
                eligible_compute_rds["pricing_model"] != "On-Demand", "annual_on_demand_cost_usd"
            ].sum()
        )
        covered_after = float(
            eligible_compute_rds.loc[
                (eligible_compute_rds["pricing_model"] != "On-Demand")
                | (eligible_compute_rds["recommended_action"] == "Reserved Instance / Savings Plan Lock-In"),
                "annual_on_demand_cost_usd",
            ].sum()
        )
        commitment_coverage_before_pct = (covered_before / elig_spend * 100.0) if elig_spend > 0 else 0.0
        commitment_coverage_after_pct = (covered_after / elig_spend * 100.0) if elig_spend > 0 else 0.0
    else:
        commitment_coverage_before_pct = 0.0
        commitment_coverage_after_pct = 0.0

    # 5. SaaS Unit Margin & EBITDA Recovery Translation
    arr = float(company_arr_usd)
    base_gm_pct = float(baseline_gross_margin_pct)
    base_gross_profit_usd = arr * (base_gm_pct / 100.0)
    base_total_cogs_usd = arr - base_gross_profit_usd
    non_cloud_cogs_usd = max(0.0, base_total_cogs_usd - total_billed_annual)

    new_gross_profit_usd = base_gross_profit_usd + total_savings_usd
    new_gm_pct = (new_gross_profit_usd / arr * 100.0) if arr > 0 else base_gm_pct
    gm_expansion_pct_pts = new_gm_pct - base_gm_pct
    gm_expansion_bps = gm_expansion_pct_pts * 100.0

    cloud_pct_of_arr_before = (total_billed_annual / arr * 100.0) if arr > 0 else 0.0
    cloud_pct_of_arr_after = (post_remediation_spend_usd / arr * 100.0) if arr > 0 else 0.0

    # Identify #1 biggest waste source by Environment x Service Type for executive narrative
    actionable_df = work[work["annual_savings_usd"] > 0]
    if not actionable_df.empty:
        env_svc_grp = (
            actionable_df.groupby(["environment", "service_type"], as_index=False)["annual_savings_usd"]
            .sum()
            .sort_values("annual_savings_usd", ascending=False)
        )
        top_hotspot_env = str(env_svc_grp.iloc[0]["environment"])
        top_hotspot_svc = str(env_svc_grp.iloc[0]["service_type"])
        top_hotspot_usd = float(env_svc_grp.iloc[0]["annual_savings_usd"])
    else:
        top_hotspot_env = "None"
        top_hotspot_svc = "None"
        top_hotspot_usd = 0.0

    kpis = {
        "total_resources": int(len(work)),
        "actionable_resources": int((work["annual_savings_usd"] > 0).sum()),
        "spiky_protected_count": int(work["is_spiky_protected"].sum()),
        "annual_billed_spend_usd": round(total_billed_annual, 2),
        "monthly_billed_spend_usd": round(total_billed_annual / 12.0, 2),
        "annual_od_equiv_spend_usd": round(total_od_equiv_annual, 2),
        "existing_commitment_savings_usd": round(existing_commitment_savings_usd, 2),
        "total_annual_savings_usd": round(total_savings_usd, 2),
        "total_monthly_savings_usd": round(total_savings_usd / 12.0, 2),
        "post_remediation_annual_spend_usd": round(post_remediation_spend_usd, 2),
        "identified_waste_rate_pct": round(waste_rate_pct, 2),
        "industry_waste_benchmark_range": "27.0% – 32.0% (Flexera 2026 Median: 29.0%)",
        "industry_waste_midpoint_pct": 29.0,
        # 3 Remediation Buckets
        "zombie_termination_savings_usd": round(zombie_waste_usd, 2),
        "zombie_termination_count": int(term_mask.sum()),
        "rightsizing_savings_usd": round(rightsize_waste_usd, 2),
        "rightsizing_count": int(rightsize_mask.sum()),
        "commitment_lockin_savings_usd": round(ondemand_premium_usd, 2),
        "commitment_lockin_count": int(sp_mask.sum()),
        "healthy_count": int((work["recommended_action"] == "Healthy / Optimized Baseline").sum()),
        # Spend Efficiency Breakdown
        "productive_utilized_spend_usd": productive_utilized_spend_usd,
        "engineering_buffer_spend_usd": engineering_buffer_spend_usd,
        # ESR & Commitment Coverage
        "baseline_esr_pct": round(baseline_esr_pct, 2),
        "optimized_esr_pct": round(optimized_esr_pct, 2),
        "esr_expansion_pct": round(esr_expansion_pct, 2),
        "commitment_coverage_before_pct": round(commitment_coverage_before_pct, 1),
        "commitment_coverage_after_pct": round(commitment_coverage_after_pct, 1),
        # SaaS Gross Margin & EBITDA Translation
        "company_arr_usd": round(arr, 2),
        "baseline_gross_margin_pct": round(base_gm_pct, 2),
        "new_gross_margin_pct": round(new_gm_pct, 2),
        "gross_margin_expansion_pct_pts": round(gm_expansion_pct_pts, 2),
        "gross_margin_expansion_bps": round(gm_expansion_bps, 0),
        "baseline_gross_profit_usd": round(base_gross_profit_usd, 2),
        "new_gross_profit_usd": round(new_gross_profit_usd, 2),
        "non_cloud_cogs_usd": round(non_cloud_cogs_usd, 2),
        "cloud_pct_of_arr_before": round(cloud_pct_of_arr_before, 2),
        "cloud_pct_of_arr_after": round(cloud_pct_of_arr_after, 2),
        # Top Waste Hotspot
        "top_hotspot_env": top_hotspot_env,
        "top_hotspot_svc": top_hotspot_svc,
        "top_hotspot_usd": round(top_hotspot_usd, 2),
        # Simulation Parameters
        "headroom_buffer_pct": float(headroom_buffer_pct),
        "commitment_term": commitment_term,
        "commitment_discount_pct": round(sp_discount * 100.0, 1),
    }

    return work, kpis


def _build_empty_kpis(
    company_arr_usd: float,
    baseline_gross_margin_pct: float,
    headroom_buffer_pct: float,
    commitment_term: str,
) -> Dict[str, Any]:
    return {
        "total_resources": 0,
        "actionable_resources": 0,
        "spiky_protected_count": 0,
        "annual_billed_spend_usd": 0.0,
        "monthly_billed_spend_usd": 0.0,
        "annual_od_equiv_spend_usd": 0.0,
        "existing_commitment_savings_usd": 0.0,
        "total_annual_savings_usd": 0.0,
        "total_monthly_savings_usd": 0.0,
        "post_remediation_annual_spend_usd": 0.0,
        "identified_waste_rate_pct": 0.0,
        "industry_waste_benchmark_range": "27.0% – 32.0% (Flexera 2026 Median: 29.0%)",
        "industry_waste_midpoint_pct": 29.0,
        "zombie_termination_savings_usd": 0.0,
        "zombie_termination_count": 0,
        "rightsizing_savings_usd": 0.0,
        "rightsizing_count": 0,
        "commitment_lockin_savings_usd": 0.0,
        "commitment_lockin_count": 0,
        "healthy_count": 0,
        "productive_utilized_spend_usd": 0.0,
        "engineering_buffer_spend_usd": 0.0,
        "baseline_esr_pct": 0.0,
        "optimized_esr_pct": 0.0,
        "esr_expansion_pct": 0.0,
        "commitment_coverage_before_pct": 0.0,
        "commitment_coverage_after_pct": 0.0,
        "company_arr_usd": float(company_arr_usd),
        "baseline_gross_margin_pct": float(baseline_gross_margin_pct),
        "new_gross_margin_pct": float(baseline_gross_margin_pct),
        "gross_margin_expansion_pct_pts": 0.0,
        "gross_margin_expansion_bps": 0.0,
        "baseline_gross_profit_usd": float(company_arr_usd * baseline_gross_margin_pct / 100.0),
        "new_gross_profit_usd": float(company_arr_usd * baseline_gross_margin_pct / 100.0),
        "non_cloud_cogs_usd": float(company_arr_usd * (1.0 - baseline_gross_margin_pct / 100.0)),
        "cloud_pct_of_arr_before": 0.0,
        "cloud_pct_of_arr_after": 0.0,
        "top_hotspot_env": "N/A",
        "top_hotspot_svc": "N/A",
        "top_hotspot_usd": 0.0,
        "headroom_buffer_pct": float(headroom_buffer_pct),
        "commitment_term": commitment_term,
        "commitment_discount_pct": 32.0,
    }


def build_remediation_export_df(evaluated_df: pd.DataFrame) -> pd.DataFrame:
    """
    Formats the prioritized remediation matrix with clean, human-readable columns
    ranked by 12-Month Cash Savings (Descending) for executive review and CSV export.
    """
    if evaluated_df.empty:
        return pd.DataFrame()

    actionable = evaluated_df[evaluated_df["annual_savings_usd"] > 0].copy()
    actionable = actionable.sort_values("annual_savings_usd", ascending=False)

    formatted = pd.DataFrame(
        {
            "Cluster ID": actionable["cluster_id"],
            "Environment": actionable["environment"],
            "Business Unit": actionable["business_unit"],
            "Service & Current Tier": actionable["service_type"] + " (" + actionable["instance_tier"] + ")",
            "Pricing Model": actionable["pricing_model"],
            "Avg / P95 Utilization": (
                actionable["avg_cpu_pct"].map(lambda x: f"{x:.1f}% Avg")
                + " | "
                + actionable["dominant_p95_pct"].map(lambda x: f"{x:.1f}% P95")
            ),
            "Current Annual Cost ($)": actionable["annual_billed_cost_usd"].round(2),
            "Recommended Action": actionable["recommended_action"],
            "Target Tier / Fix": actionable["target_tier_fix"],
            "Risk Level": actionable["risk_level"],
            "12-Month Cash Savings ($)": actionable["annual_savings_usd"].round(2),
            "Plain-English Justification": actionable["plain_english_justification"],
        }
    )
    return formatted.reset_index(drop=True)