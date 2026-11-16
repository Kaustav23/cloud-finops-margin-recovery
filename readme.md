# ⚡ Cloud FinOps & Unit Margin Recovery Engine
### Zombie Infrastructure & EBITDA Erosion Analytics

**Author:** Kaustav Goswami ([GitHub: Kaustav23](https://www.google.com/search?q=https://github.com/Kaustav23))

An executive-grade **Cloud FinOps, Infrastructure Right-Sizing, and SaaS Unit Margin Recovery** analytics platform built in Python and Streamlit. This application bridges the gap between **VP of Engineering infrastructure telemetry** (P95/P99 CPU, RAM, IOPS, and diurnal burst headroom) and **CFO SaaS unit economics** (Cost of Goods Sold, Gross Margin basis-point expansion, 12-Month Run-Rate EBITDA recovery, and Effective Savings Rate).

---

## 🎯 Executive Problem Statement

According to the [Flexera State of the Cloud Report](https://www.flexera.com/about-us/press-center/new-flexera-report-finds-84-percent-of-organizations-struggle-to-manage-cloud-spend) and [multi-year Cloud Waste synthesis (2020–2026)](https://ideatives.com/briefs/cloud-cost/), enterprises waste **27% to 32% of their total cloud spend** every year (**29%** median in 2026), while **84%** of organizations cite managing cloud spend as their #1 cloud challenge. Similarly, the [HashiCorp State of Cloud Strategy Survey](https://www.hashicorp.com/en/blog/new-survey-shows-broad-cloud-waste-hashicorp-terraform-can-help) found that **94%** of enterprises incur avoidable cloud spend driven by idle/orphaned resources (**66%**) and over-provisioned instances (**59%**).

However, traditional cloud cost tools fail in practice for two reasons:
1. **Engineering Distrust (Dangerous Average-CPU Rules):** Naive tools flag any server with `<20%` average CPU as "idle." As proven by [Cortez et al. (Microsoft Research *Resource Central*, ACM SOSP '17)](https://www.microsoft.com/en-us/research/wp-content/uploads/2017/10/Resource-Central-SOSP17.pdf), production workloads are heavily skewed and diurnal—a service averaging 14% CPU can spike to 78% at P95 and 94% at P99 during peak business hours. Downsizing or terminating based on averages causes production outages.
2. **Financial Disconnect:** Engineering dashboards report vCPUs and gigabytes, whereas CFOs and boards measure **SaaS Gross Margin (% and basis points)**, **12-Month Run-Rate EBITDA**, and the [FinOps Foundation's Effective Savings Rate (ESR)](https://www.finops.org/framework/capabilities/rate-optimization/).

This engine solves both problems simultaneously by combining **P95/P99 safety-buffered telemetry diagnostics** with a real-time **CFO Unit Margin & EBITDA Recovery simulator**.

---

## 🏗️ System Architecture

```
+-----------------------------------------------------------------------------------+
|                   1. EMPIRICAL TELEMETRY & PRICING LAYER                          |
|  generate_empirical_data.py  --->  cloud_telemetry_logs.csv (3,200 Cloud Assets)  |
|  - Cortez et al. (SOSP '17) & Reiss et al. (SoCC '12) Log-Normal / Diurnal Traces |
|  - Documented AWS us-east-1 Pricing (EC2 m6i/r6i/g5, RDS db.m6i/r6i, EBS gp3/io2) |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                  2. DECOPLED QUANTITATIVE FINOPS ENGINE (finops_engine.py)        |
|                                                                                   |
|  +------------------------+  +-------------------------+  +--------------------+  |
|  | Bucket 1: Zombie Logic |  | Bucket 2: P95/P99 Safe  |  | Bucket 3: RI / SP  |  |
|  | - Unattached EBS >=14d |  |   Right-Sizing Engine   |  |   Rate Lock-In     |  |
|  | - P95 CPU <5% & RAM    |  | - Dominant P95 * (1+B)  |  | - Uptime >= 95%    |  |
|  |   <10% & NetIO <0.5    |  | - P99 Post-Resize <=92% |  | - Load CV <= 0.35  |  |
|  | - Protects Spiky Prod! |  | - 1-Step / 2-Step Tiers |  | - 1-Yr(32%)/3-Yr   |  |
|  +------------------------+  +-------------------------+  +--------------------+  |
|                                         |                                         |
|                                         v                                         |
|         SaaS COGS Reduction ---> Gross Margin (+bps) & 12-Mo EBITDA Bridge        |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                3. EXECUTIVE STREAMLIT DASHBOARD (app.py)                          |
|  - 5 Plain-English Executive KPI Cards (Spend, Waste %, Cash Saved, GM Lift, ESR) |
|  - Tab 1: CFO Verdict, Spend Waterfall & Efficiency Donut                         |
|  - Tab 2: VP Eng Quadrant Scatter (Spiky Protection Proof) & Waste Heatmap        |
|  - Tab 3: 3-Bucket Action Plan & 1-Click CSV Remediation Export                   |
|  - Tab 4: Full Academic Citations, LaTeX Equations & Audit Trail                  |
+-----------------------------------------------------------------------------------+
```

---

## 📚 Summary of Empirical Research Foundation

| Benchmark / Model Component | Empirical Metric / Rule | Primary Source Citation |
| :--- | :--- | :--- |
| **Enterprise Cloud Waste Rate** | **27% – 32%** of total cloud spend wasted annually (**29%** in 2026; **27%** in 2025) | [Flexera State of the Cloud Report](https://www.flexera.com/about-us/press-center/new-flexera-report-finds-84-percent-of-organizations-struggle-to-manage-cloud-spend) & [Ideatives Cloud Waste Brief](https://ideatives.com/briefs/cloud-cost/) |
| **Waste Root-Cause Split** | **94%** report avoidable spend (**66%** idle resources, **59%** over-provisioning) | [HashiCorp State of Cloud Strategy Survey](https://www.hashicorp.com/en/blog/new-survey-shows-broad-cloud-waste-hashicorp-terraform-can-help) |
| **Workload Utilization & Tail Spikes** | Heavy-tailed CPU/RAM distributions; diurnal P95/P99 burst protection & CV stability | [Cortez et al. (2017), *Resource Central* (Microsoft Research / ACM SOSP '17)](https://www.microsoft.com/en-us/research/wp-content/uploads/2017/10/Resource-Central-SOSP17.pdf) |
| **Multi-Resource Skewness** | Decoupled CPU vs. memory bottlenecks across compute, memory, and GPU clusters | [Reiss et al. (2012), *Google Trace Analysis* (ACM SoCC '12 Test of Time Award)](https://www.pdl.cmu.edu/PDL-FTP/CloudComputing/googletrace-socc2012.pdf) |
| **Right-Sizing Safety Guardrails** | P95 peak utilization + configurable **15%–50% headroom buffer** (default **30%**) | [AWS Well-Architected Framework — Cost Optimization Pillar](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html) |
| **Effective Savings Rate (ESR)** | $\text{ESR} = \text{Total Net Savings} / \text{On-Demand Equivalent Spend}$ | [FinOps Foundation Rate Optimization](https://www.finops.org/framework/capabilities/rate-optimization/) & [FinOps ESR Playbook](https://www.finout.io/blog/effective-savings-rate-measure-commitment-savings) |
| **Public Cloud Instance & Storage Pricing** | AWS `us-east-1` On-Demand & Savings Plans (`m6i`, `r6i`, `g5`, `db.m6i`, `db.r6i`, `gp3`, `io2`) | [AWS EC2 On-Demand Pricing](https://aws.amazon.com/ec2/pricing/on-demand/), [AWS Savings Plans](https://aws.amazon.com/savingsplans/compute-pricing/), [AWS RDS Pricing](https://aws.amazon.com/rds/custom/pricing/), [AWS EBS Pricing](https://aws.amazon.com/ebs/pricing/) |

*(See [METHODOLOGY\_AND\_CITATIONS.md](https://www.google.com/search?q=./METHODOLOGY_AND_CITATIONS.md) for full mathematical derivations and hourly pricing tables.)*

---

## 📖 Plain-English KPI Glossary (For Non-Technical Stakeholders & Recruiters)

* **Annualized Cloud Spend (Run-Rate):** What the company is currently on track to pay cloud providers (AWS/Azure/GCP) over 12 months for servers, databases, storage, and AI GPUs.
* **Zombie Infrastructure (`Immediate Termination`):** Cloud resources that are turned on and generating a monthly bill but doing zero useful work—such as unattached hard drives (`Block Storage EBS`) left behind after a virtual machine was deleted, or forgotten `Development` servers with `<5%` peak activity for over two weeks.
* **P95 Peak Utilization & Safety Headroom Buffer:** `P95 Utilization` is the server load level that is only exceeded 5% of the time (the top 36 hours of a 720-hour month). Adding a **30% Headroom Buffer** guarantees that even during peak traffic spikes, a downsized server still keeps at least 30% spare breathing room so customer applications never slow down or crash.
* **Savings Plans / Reserved Instances (`RI/SP Lock-In`):** Just like signing a 1-year or 3-year lease on an apartment is cheaper than paying night-by-night hotel rates (`On-Demand`), committing steady 24/7 production servers to a 1-Year or 3-Year Savings Plan cuts the hourly price by **32% to 54%** with zero code changes.
* **Gross Margin Basis Points (`bps`):** One percentage point (`+1.0%`) equals `100 basis points (+100 bps)`. Because cloud hosting is a direct Cost of Goods Sold (COGS) for software companies, cutting `$1.85M` in cloud waste on `$25M` ARR directly expands Gross Margin by `+7.4% (+740 bps)` and adds `$1.85M` straight to EBITDA profit.
* **Effective Savings Rate (ESR):** The [FinOps Foundation's](https://www.finops.org/framework/capabilities/rate-optimization/) single overarching efficiency score showing total dollars saved (from both commitment discounts and waste elimination) divided by what the infrastructure would have cost at full retail On-Demand prices.

---

## 📂 Repository File Structure

```text
├── requirements.txt               # Pinned, lightweight Streamlit Cloud dependencies
├── generate_empirical_data.py     # Deterministic (seed=42) telemetry generator (3,200 records)
├── cloud_telemetry_logs.csv       # Pre-generated 30-day cloud telemetry dataset (loads out-of-the-box)
├── finops_engine.py               # Pure quantitative FinOps, P95 right-sizing & EBITDA engine
├── app.py                         # Flagship interactive Streamlit dashboard (4 executive tabs)
├── METHODOLOGY_AND_CITATIONS.md   # Complete academic citations, AWS rate tables & LaTeX formulas
└── README.md                      # Executive overview, architecture & deployment guide
```

---

## 🚀 Local Execution & Streamlit Cloud Deployment

### 1. Run Locally on Windows PowerShell
```powershell
py -m pip install -r requirements.txt
py generate_empirical_data.py
py -m streamlit run app.py
```

### 2. Run Locally on macOS / Linux
```bash
pip install -r requirements.txt
python3 generate_empirical_data.py
streamlit run app.py
```

### 3. Deploy to Streamlit Community Cloud
1. Push all 7 files to a public GitHub repository under your account (`Kaustav23`).
2. Log in to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click **New app**, select your repository and branch (`main`), and set **Main file path** to `app.py`.
4. Click **Deploy** — `cloud_telemetry_logs.csv` is pre-bundled in the root directory so the dashboard launches instantaneously.
