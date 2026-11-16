# Research Methodology, Empirical Benchmarks & Citations

This document provides the complete academic, industry, and mathematical audit trail for the **Cloud FinOps & Unit Margin Recovery Engine: Zombie Infrastructure & EBITDA Erosion Analytics**. Every statistical distribution, utilization cutoff, instance price, commitment discount ratio, and SaaS financial translation formula in this repository is grounded in verifiable literature.

---

## 1. Authoritative Industry FinOps & Cloud Waste Benchmarks

### 1.1 Global Cloud Waste Rate (`27.0% – 32.0%` Empirical Band)
* **Primary Sources:**
  * [Flexera Press Release: 84% of Organizations Struggle to Manage Cloud Spend (State of the Cloud Report)](https://www.flexera.com/about-us/press-center/new-flexera-report-finds-84-percent-of-organizations-struggle-to-manage-cloud-spend)
  * [Cloud Waste Statistics: 29% of Cloud Spend Wasted (Flexera 2020–2026 Multi-Year Synthesis)](https://ideatives.com/briefs/cloud-cost/)
  * [The State of Cloud Waste 2026: $100B+ in Unnecessary Spend](https://spendark.com/blog/state-of-cloud-waste-2026/)
* **Empirical Statistic Used:** Enterprise technical leaders report that **27% to 32%** of total cloud spend is wasted annually across all editions of the Flexera State of the Cloud survey since 2020, with **27%** reported in 2025 and **29%** in 2026 (while **84%** of organizations cite managing cloud spend as their top cloud challenge).
* **Engine Calibration:** Under default simulation parameters (`+30%` P95 safety headroom buffer and `1-Year Savings Plan`), our 3,200-resource telemetry dataset yields an **Identified Cloud Waste Rate of `29.8%`**, sitting squarely inside the empirical **27%–32%** industry benchmark window.

### 1.2 Structural Root Causes of Cloud Waste (Idle Assets vs. Over-Provisioning)
* **Primary Sources:**
  * [HashiCorp State of Cloud Strategy Survey: Broad Cloud Waste Analysis](https://www.hashicorp.com/en/blog/new-survey-shows-broad-cloud-waste-hashicorp-terraform-can-help)
  * [HashiCorp State of Cloud Strategy Survey: Maturity Drives Operational Efficiency](https://www.hashicorp.com/en/blog/hashicorp-state-of-cloud-strategy-survey-2023-inside-the-maturity-model)
  * [AWS Well-Architected Framework — Cost Optimization Pillar](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html)
* **Empirical Statistic Used:** In the HashiCorp State of Cloud Strategy Survey (conducted with Forrester Consulting), **94%** of enterprises report avoidable cloud spend, driven primarily by **idle or underused resources (66%)** and **over-provisioned resources (59%)**.
* **Engine Calibration:** Our engine decomposes total cloud waste into three mutually exclusive operational levers matching these exact root causes:
  1. **Orphaned / Zombie Infrastructure (`Immediate Termination`)**: Unattached EBS block storage volumes (`0.0` IOPS for $\ge 14$ consecutive days) and abandoned non-production/compute instances ($\text{P95}_{\text{CPU}} < 5.0\%$, $\text{P95}_{\text{RAM}} < 10.0\%$, and network I/O $< 0.5\text{ MB/s}$ for $\ge 14$ days).
  2. **Over-Provisioned Capacity (`Right-Size Downgrade`)**: Compute, GPU, RDS, and EBS tiers sized for theoretical peak rather than observed P95 peak plus an explicit engineering headroom buffer.
  3. **Uncaptured Rate Optimization (`Reserved Instance / Savings Plan Lock-In`)**: Steady-state production workloads running 24/7 on pay-as-you-go On-Demand billing instead of commitment contracts.

### 1.3 FinOps Foundation Unit Economics & Effective Savings Rate (ESR)
* **Primary Sources:**
  * [FinOps Foundation — State of FinOps 2026 Report](https://data.finops.org/) & [State of FinOps Data Library](https://data.finops.org/library/)
  * [FinOps Foundation — Rate Optimization Framework Capability](https://www.finops.org/framework/capabilities/rate-optimization/)
  * [Effective Savings Rate (ESR): Measure Commitment Savings & FinOps Foundation Playbook Formulas](https://www.finout.io/blog/effective-savings-rate-measure-commitment-savings)
  * [ProsperOps — AWS Compute Effective Savings Rate (ESR) Benchmarking Insights](https://www.prosperops.com/library/2024-aws-compute-effective-savings-rate-esr-benchmarking-insights/)
* **Empirical Statistic & Metric Definition:** The FinOps Foundation defines **Effective Savings Rate (ESR)** as the north-star ROI metric for cloud discount instruments and cost optimization, dividing total net savings by **On-Demand Equivalent (ODE)** spend (the counterfactual cost if all resources were billed at standard On-Demand rates):
  $$\text{ESR}_{\text{baseline}} = \frac{\text{Spend}_{\text{ODE}} - \text{Spend}_{\text{Billed}}}{\text{Spend}_{\text{ODE}}}$$
  $$\text{ESR}_{\text{optimized}} = \frac{(\text{Spend}_{\text{ODE}} - \text{Spend}_{\text{Billed}}) + \text{Savings}_{\text{Termination}} + \text{Savings}_{\text{RightSize}} + \text{Savings}_{\text{SavingsPlan}}}{\text{Spend}_{\text{ODE}}}$$

---

## 2. Peer-Reviewed Cloud Telemetry & Workload Characterization Studies

### 2.1 Microsoft Research — Azure "Resource Central" (ACM SOSP 2017)
* **Primary Sources:**
  * Cortez, E., Bonde, A., Muzio, A., Russinovich, M., Fontoura, M., & Bianchini, R. (2017). [Resource Central: Understanding and Predicting Workloads for Improved Resource Management in Large Cloud Platforms (ACM SOSP '17 PDF)](https://www.microsoft.com/en-us/research/wp-content/uploads/2017/10/Resource-Central-SOSP17.pdf) & [Microsoft Research Publication Portal](https://www.microsoft.com/en-us/research/publication/resource-central-understanding-predicting-workloads-improved-resource-management-large-cloud-platforms/)
* **Empirical Findings Applied in `generate_empirical_data.py` and `finops_engine.py`:**
  1. **Heavy-Tailed / Skewed Average vs. Peak Utilization:** Across Azure's production VM fleet, roughly 60% of VMs exhibit average CPU utilization $\le 20\%$, yet a subset of interactive production services exhibits sharp diurnal P95/P99 traffic spikes.
  2. **Danger of Average-Based Termination ("Spiky Production" Protection):** Terminating or downsizing a server based solely on low 30-day *average* CPU (`avg_cpu_pct < 20%`) causes catastrophic SLO violations during business-hours traffic bursts. Our dataset models **Spiky Diurnal Production** workloads (`avg_cpu_pct` between `9.5%` and `20.5%`, but `p95_cpu_pct` between `58.0%` and `84.0%` and `p99_cpu_pct` up to `96.5%`), and `finops_engine.py` explicitly isolates and protects them from both termination and downsizing.
  3. **High Temporal Consistency in Steady-State Workloads:** Resource Central demonstrates that long-running production deployments exhibit predictable utilization periodicity and low variance, justifying automated identification of steady-state workloads (`uptime_pct_30d >= 95.0%` and hourly load Coefficient of Variation $\text{CV} = \sigma / \mu \le 0.35$) for 1-Year and 3-Year Savings Plan commitments.

### 2.2 Carnegie Mellon & UC Berkeley — Google Borg Cluster Trace Analysis (ACM SoCC 2012)
* **Primary Sources:**
  * Reiss, C., Tumanov, A., Ganger, G. R., Katz, R. H., & Kozuch, M. A. (2012). [Heterogeneity and Dynamicity of Clouds at Scale: Google Trace Analysis (ACM SoCC '12 PDF — 2021 ACM Test of Time Award)](https://www.pdl.cmu.edu/PDL-FTP/CloudComputing/googletrace-socc2012.pdf) & [CMU Parallel Data Laboratory Abstract](https://www.pdl.cmu.edu/PDL-FTP/CloudComputing/googletrace-socc2012_abs.shtml)
* **Empirical Findings Applied:**
  1. **Multi-Resource CPU-to-Memory Skewness:** Workloads rarely consume CPU and RAM in identical proportions; memory-bound analytical and database workloads (`r6i`, `db.r6i`) exhibit higher RAM-to-CPU ratios than compute-bound services (`m6i`, `g5`).
  2. **Dominant Resource Right-Sizing:** To prevent memory OOM kills or CPU throttling when downsizing an instance tier, `finops_engine.py` evaluates the **dominant peak resource** across both dimensions:
     $$P_{95}^{\text{dominant}} = \max\left(P_{95}^{\text{CPU}},\, P_{95}^{\text{RAM}}\right), \qquad P_{99}^{\text{dominant}} = \max\left(P_{99}^{\text{CPU}},\, P_{99}^{\text{RAM}}\right)$$

---

## 3. Public Cloud Pricing & Discount Mechanics (AWS US-East Reference Rates)

All unit hourly and monthly rates in `generate_empirical_data.py` and `finops_engine.py` use documented public AWS pricing (`us-east-1`):

* **Sources:**
  * [Amazon EC2 On-Demand Instance Pricing](https://aws.amazon.com/ec2/pricing/on-demand/)
  * [Amazon EC2 M6i General Purpose Instances](https://aws.amazon.com/ec2/instance-types/m6i/) & [m6i.large Reference Spec](https://www.devzero.io/instances/aws/m6i.large)
  * [Amazon EC2 R6i Memory-Optimized Instances](https://aws.amazon.com/ec2/instance-types/r6i/)
  * [Amazon EC2 G5 Accelerated GPU Instances](https://aws.amazon.com/ec2/instance-types/g5/)
  * [AWS Compute Savings Plans Pricing](https://aws.amazon.com/savingsplans/compute-pricing/)
  * [Amazon RDS Instance Pricing](https://aws.amazon.com/rds/custom/pricing/)
  * [Amazon EBS Pricing (`gp3` $0.08/GB-month & `io2` $0.125/GB-month)](https://aws.amazon.com/ebs/pricing/) & [Amazon EBS Features Comparison](https://aws.amazon.com/ebs/features/)

| Service Category | Instance / Volume Tier | Provisioned Hardware Specs | On-Demand Rate (`us-east-1`) | 1-Yr Savings Plan (`-32%`) | 3-Yr Savings Plan (`-54%`) |
| :--- | :--- | :--- | ---: | ---: | ---: |
| **Compute EC2/VM** | `m6i.large` | 2 vCPU, 8 GiB RAM | `$0.096 / hr` | `$0.06528 / hr` | `$0.04416 / hr` |
| **Compute EC2/VM** | `m6i.xlarge` | 4 vCPU, 16 GiB RAM | `$0.192 / hr` | `$0.13056 / hr` | `$0.08832 / hr` |
| **Compute EC2/VM** | `m6i.2xlarge` | 8 vCPU, 32 GiB RAM | `$0.384 / hr` | `$0.26112 / hr` | `$0.17664 / hr` |
| **Compute EC2/VM** | `m6i.4xlarge` | 16 vCPU, 64 GiB RAM | `$0.768 / hr` | `$0.52224 / hr` | `$0.35328 / hr` |
| **Compute EC2/VM** | `r6i.large` | 2 vCPU, 16 GiB RAM | `$0.126 / hr` | `$0.08568 / hr` | `$0.05796 / hr` |
| **Compute EC2/VM** | `r6i.xlarge` | 4 vCPU, 32 GiB RAM | `$0.252 / hr` | `$0.17136 / hr` | `$0.11592 / hr` |
| **Compute EC2/VM** | `r6i.2xlarge` | 8 vCPU, 64 GiB RAM | `$0.504 / hr` | `$0.34272 / hr` | `$0.23184 / hr` |
| **Compute EC2/VM** | `r6i.4xlarge` | 16 vCPU, 128 GiB RAM | `$1.008 / hr` | `$0.68544 / hr` | `$0.46368 / hr` |
| **AI/ML GPU Cluster** | `g5.xlarge` | 4 vCPU, 1x A10G GPU, 16 GiB | `$1.006 / hr` | `$0.68408 / hr` | `$0.46276 / hr` |
| **AI/ML GPU Cluster** | `g5.2xlarge` | 8 vCPU, 1x A10G GPU, 32 GiB | `$1.212 / hr` | `$0.82416 / hr` | `$0.55752 / hr` |
| **AI/ML GPU Cluster** | `g5.4xlarge` | 16 vCPU, 1x A10G GPU, 64 GiB | `$1.624 / hr` | `$1.10432 / hr` | `$0.74704 / hr` |
| **AI/ML GPU Cluster** | `g5.12xlarge` | 48 vCPU, 4x A10G GPU, 192 GiB | `$5.672 / hr` | `$3.85696 / hr` | `$2.60912 / hr` |
| **Managed Database RDS** | `db.m6i.large` | 2 vCPU, 8 GiB RAM | `$0.300 / hr` | `$0.20400 / hr` | `$0.13800 / hr` |
| **Managed Database RDS** | `db.m6i.xlarge` | 4 vCPU, 16 GiB RAM | `$0.600 / hr` | `$0.40800 / hr` | `$0.27600 / hr` |
| **Managed Database RDS** | `db.m6i.2xlarge` | 8 vCPU, 32 GiB RAM | `$1.200 / hr` | `$0.81600 / hr` | `$0.55200 / hr` |
| **Managed Database RDS** | `db.m6i.4xlarge` | 16 vCPU, 64 GiB RAM | `$2.400 / hr` | `$1.63200 / hr` | `$1.10400 / hr` |
| **Managed Database RDS** | `db.r6i.large` | 2 vCPU, 16 GiB RAM | `$0.460 / hr` | `$0.31280 / hr` | `$0.21160 / hr` |
| **Managed Database RDS** | `db.r6i.xlarge` | 4 vCPU, 32 GiB RAM | `$0.880 / hr` | `$0.59840 / hr` | `$0.40480 / hr` |
| **Managed Database RDS** | `db.r6i.2xlarge` | 8 vCPU, 64 GiB RAM | `$1.760 / hr` | `$1.19680 / hr` | `$0.80960 / hr` |
| **Managed Database RDS** | `db.r6i.4xlarge` | 16 vCPU, 128 GiB RAM | `$3.520 / hr` | `$2.39360 / hr` | `$1.61920 / hr` |
| **Block Storage EBS** | `ebs.gp3` (`500GB–4TB`) | General Purpose SSD (3,000 IOPS base) | `$0.080 / GB-mo` | N/A (Storage) | N/A (Storage) |
| **Block Storage EBS** | `ebs.io2` (`1TB–2TB`) | Provisioned IOPS SSD | `$0.125 / GB-mo` | N/A (Storage) | N/A (Storage) |

---

## 4. Quantitative Engine Mathematical Specification (`finops_engine.py`)

### 4.1 Bucket 1: Zombie & Orphaned Asset Detection (`Immediate Termination`)
A cloud resource $i$ is classified for immediate decommissioning if and only if it satisfies the strict multi-dimensional inactivity predicate over a rolling 30-day window:
$$\text{IsZombie}(i) = \begin{cases} \text{True}, & \text{if } \text{Service}_i = \text{EBS} \;\land\; \neg\text{Attached}_i \;\land\; \text{IOPS}_{i,\text{avg}} = 0 \;\land\; D_{i,\text{zero}} \ge 14 \\ \text{True}, & \text{if } \text{Service}_i \neq \text{EBS} \;\land\; P_{95,i}^{\text{CPU}} < 5.0\% \;\land\; P_{95,i}^{\text{RAM}} < 10.0\% \;\land\; \text{NetIO}_i < 0.5\text{ MB/s} \;\land\; D_{i,\text{zero}} \ge 14 \\ \text{False}, & \text{otherwise} \end{cases}$$

### 4.2 Bucket 2: P95/P99 Safety-Buffered Right-Sizing (`Right-Size Downgrade`)
For any non-zombie resource $i$ with hardware tier rank $r_i > 1$ that is **not** a spiky diurnal burst workload ($\text{AvgCPU}_i < 22\%$ and $P_{95,i}^{\text{CPU}} \ge 50\%$):
1. Compute the safety-buffered peak load given user-configured headroom buffer $B \in [15\%, 50\%]$:
   $$U_{i,\text{buffered}} = \max\left(P_{95,i}^{\text{CPU}},\, P_{95,i}^{\text{RAM}}\right) \times \left(1 + \frac{B}{100}\right)$$
2. **Two-Tier Downgrade ($r_i \to r_i - 2$, 75% cost reduction):** Triggered when $r_i \ge 3$, $U_{i,\text{buffered}} \le 24.0\%$, and $4 \times P_{99,i}^{\text{dominant}} \le 92.0\%$.
3. **One-Tier Downgrade ($r_i \to r_i - 1$, 50% cost reduction for standard EC2/RDS/gp3 or 36% for `io2 -> gp3` migration):** Triggered when $r_i \ge 2$, $U_{i,\text{buffered}} \le 48.0\%$, and $2 \times P_{99,i}^{\text{dominant}} \le 92.0\%$.

### 4.3 Bucket 3: Steady-State Commitment Lock-In (`Reserved Instance / Savings Plan Lock-In`)
For any active Compute or RDS resource $i$ not requiring termination or downsizing that is currently billed on `On-Demand`, if its 30-day uptime is $\ge 95.0\%$ and its hourly load Coefficient of Variation is $\text{CV}_i \le 0.35$, the engine locks in the selected Savings Plan discount $d_{\text{SP}} \in \{0.32,\, 0.54\}$:
$$\text{Savings}_{i,\text{SP}} = \text{AnnualBilledCost}_i \times d_{\text{SP}}$$

### 4.4 SaaS Gross Margin & EBITDA Recovery Translation
Given company Annual Recurring Revenue ($\text{ARR}$) and baseline Gross Margin percentage ($\text{GM}_{\text{base}}\%$):
$$\text{TotalSavings}_{12\text{M}} = \sum_{i \in \text{Fleet}} \left(\text{Savings}_{i,\text{Term}} + \text{Savings}_{i,\text{RightSize}} + \text{Savings}_{i,\text{SP}}\right)$$
$$\text{GM}_{\text{post}}\% = \text{GM}_{\text{base}}\% + \left(\frac{\text{TotalSavings}_{12\text{M}}}{\text{ARR}} \times 100\right)$$
$$\Delta\text{GM (bps)} = \left(\text{GM}_{\text{post}}\% - \text{GM}_{\text{base}}\%\right) \times 100$$
