"""Interactive, interview-ready product experimentation dashboard."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analysis import GUARDRAILS, analyze, binary_test

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "experiment_users.csv"
MINT, BLUE, RED, MUTED = "#7EE2B8", "#76B9F3", "#FF8F9C", "#AABBCB"

st.set_page_config(page_title="Northstar | Experiment Lab", page_icon="🧪",
                   layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html, body, [class*="css"], [data-testid="stApp"] {font-family:'DM Sans',sans-serif;}
h1,h2,h3 {font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.035em;}
[data-testid="stApp"] {background:radial-gradient(circle at 85% 0%,#12343B 0%,#07121F 42%);}
[data-testid="stSidebar"] {background:#0B1B2B;border-right:1px solid #244057;}
.block-container {padding-top:3.5rem;max-width:1400px;}
.eyebrow {color:#7EE2B8;letter-spacing:.17em;font-size:.77rem;font-weight:700;text-transform:uppercase;}
.hero {font-size:3rem;line-height:1.08;margin:.35rem 0 .5rem;color:#F4FAFB;}
.sub {color:#AABBCB;font-size:1.03rem;max-width:850px;line-height:1.6;margin-bottom:1.2rem;}
.pill {display:inline-block;padding:.38rem .72rem;border-radius:999px;background:#12383B;color:#8CE8C0;font-size:.78rem;font-weight:700;border:1px solid #25665F;}
.card {background:#102235;border:1px solid #244057;border-radius:16px;padding:1.2rem 1.35rem;margin:.4rem 0 1rem;min-height:124px;}
.card-label {color:#AABBCB;font-size:.78rem;text-transform:uppercase;letter-spacing:.1em;}
.card-value {font-family:'Space Grotesk';font-weight:700;font-size:2rem;color:#F4FAFB;margin:.35rem 0;}
.card-note {font-size:.84rem;color:#AABBCB;}
.callout {background:#192939;border-left:4px solid #FF8F9C;border-radius:8px;padding:1rem 1.2rem;color:#EAF4F6;margin:1rem 0;}
.good {border-left-color:#7EE2B8;}
div[data-testid="stMetric"] {background:#102235;border:1px solid #244057;padding:1rem;border-radius:12px;}
div[data-testid="stMetricLabel"] {color:#AABBCB;}
div[data-testid="stTabs"] button {font-weight:600;}
hr {border-color:#244057;}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)


@st.cache_data
def get_analysis(data):
    return analyze(data)


def card(label, value, note):
    st.markdown(f'<div class="card"><div class="card-label">{label}</div>'
                f'<div class="card-value">{value}</div><div class="card-note">{note}</div></div>',
                unsafe_allow_html=True)


def pct(value):
    return f"{value:.2%}"


def pp(value):
    return f"{value*100:+.2f} pp"


def base_chart(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=20, r=20, t=45, b=25),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#D8E6ED", family="DM Sans"),
                      xaxis=dict(gridcolor="#254056", zerolinecolor="#406074"),
                      yaxis=dict(gridcolor="#254056", zerolinecolor="#406074"),
                      legend=dict(orientation="h", y=1.12, x=0))
    st.plotly_chart(fig, width="stretch")


df = load_data()
r = get_analysis(df)
p = r["primary"]

with st.sidebar:
    st.markdown("### ◈ NORTHSTAR")
    st.caption("PRODUCT ANALYTICS / EXPERIMENT 01")
    st.divider()
    st.markdown("**Experiment**  ·  Guided onboarding")
    st.markdown("**Population**  ·  Eligible SaaS users")
    st.markdown("**Allocation**  ·  50 / 50 at user level")
    st.markdown("**Enrollment**  ·  Feb 1–14, 2025")
    st.markdown("**Readout**  ·  Mar 1, 2025")
    st.divider()
    st.info("Portfolio case study. All user records are **synthetic** and reproducible with a fixed random seed.")
    st.download_button("Download experiment CSV", df.to_csv(index=False),
                       file_name="synthetic_experiment_users.csv", mime="text/csv",
                       width="stretch")

st.markdown('<div class="eyebrow">Experiment readout / 01</div>', unsafe_allow_html=True)
st.markdown('<h1 class="hero">Does guided onboarding<br>turn more users into customers?</h1>', unsafe_allow_html=True)
st.markdown('<div class="sub">A user randomized A/B test of a redesigned first run experience. '
            'Explore conversion, data quality, guardrails, and a decision grounded in statistical and product risk.</div>',
            unsafe_allow_html=True)
st.markdown('<span class="pill">●  COMPLETE 14-DAY FOLLOW-UP</span>', unsafe_allow_html=True)
st.write("")

overview, integrity, segments, decision, methods = st.tabs(
    ["Overview", "Experiment quality", "Segments & cohorts", "Decision", "Methodology"])

with overview:
    a, b, c, d = st.columns(4)
    with a: card("Control conversion", pct(p.control_rate), f"{p.control_n:,} assigned users")
    with b: card("Treatment conversion", pct(p.treatment_rate), f"{p.treatment_n:,} assigned users")
    with c: card("Absolute lift", pp(p.effect), f"{p.relative_lift:+.1%} relative lift")
    with d: card("95% confidence interval", f"{p.ci_low*100:.2f}–{p.ci_high*100:.2f}", "percentage point range")

    left, right = st.columns([1.25, 1])
    with left:
        st.subheader("Primary outcome")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=["Control", "Treatment"],
                             y=[p.control_rate*100, p.treatment_rate*100],
                             marker_color=[BLUE, MINT], width=.55,
                             text=[f"{p.control_rate:.2%}", f"{p.treatment_rate:.2%}"],
                             textposition="outside", showlegend=False))
        fig.update_yaxes(title="Paid conversion within 14 days (%)", range=[0, 17])
        base_chart(fig)
        st.caption(f"Two-sided pooled z test · p = {p.p_value:.3g} · Difference CI uses Newcombe–Wilson.")
    with right:
        st.subheader("What else moved?")
        summary = pd.DataFrame([
            {"Metric": "Activation · 7d", "Control": pct(r['secondary'].control_rate),
             "Treatment": pct(r['secondary'].treatment_rate), "Difference": pp(r['secondary'].effect)},
            {"Metric": "Revenue / assigned user", "Control": f"${r['revenue']['control_mean']:.2f}",
             "Treatment": f"${r['revenue']['treatment_mean']:.2f}", "Difference": f"+${r['revenue']['effect']:.2f}"},
            *[{"Metric": k.replace('_14d', '').replace('_', ' ').title() + " · 14d",
               "Control": pct(v.control_rate), "Treatment": pct(v.treatment_rate),
               "Difference": pp(v.effect)} for k, v in r["guardrails"].items()],
        ])
        st.dataframe(summary, hide_index=True, width="stretch")
        st.markdown("**Current recommendation**")
        st.markdown('<div class="callout"><strong>Hold rollout and investigate crashes.</strong><br>'
                    'Conversion improves, but the crash rate upper confidence bound exceeds the predeclared '
                    '0.5 percentage point safety margin.</div>', unsafe_allow_html=True)

with integrity:
    st.subheader("Can we trust the assignment?")
    c1, c2, c3 = st.columns(3)
    c1.metric("Sample ratio mismatch", "Pass" if r["srm"]["pass"] else "Fail",
              f"p = {r['srm']['p_value']:.3f}")
    c2.metric("Treatment allocation", pct(r["srm"]["treatment_share"]), "expected 50%")
    c3.metric("Max. baseline imbalance", f"{r['balance'].smd.abs().max():.3f}", "threshold |SMD| < 0.10")
    st.caption("SRM uses a 1 degree of freedom chi-square test with a conservative p < 0.001 alarm. "
               "Balance checks use only attributes recorded before assignment; small differences are expected by chance.")

    daily = df.groupby(["assigned_at", "variant"]).size().unstack(fill_value=0).reset_index()
    fig = go.Figure()
    for variant, color in [("control", BLUE), ("treatment", MINT)]:
        fig.add_trace(go.Scatter(x=daily.assigned_at, y=daily[variant], mode="lines+markers",
                                 name=variant.title(), line=dict(color=color, width=3)))
    fig.update_yaxes(title="Users assigned")
    fig.update_xaxes(title="Assignment date")
    base_chart(fig)
    st.markdown("#### Pre-treatment balance by category")
    balance_table = r["balance"].copy()
    balance_table["control_share"] = balance_table.control_share.map(lambda x: f"{x:.1%}")
    balance_table["treatment_share"] = balance_table.treatment_share.map(lambda x: f"{x:.1%}")
    balance_table["smd"] = balance_table.smd.map(lambda x: f"{x:+.3f}")
    st.dataframe(balance_table, hide_index=True, width="stretch")

with segments:
    st.subheader("Who responded to the change?")
    st.caption("Exploratory cuts of the randomized population. These comparisons do not establish treatment-effect "
               "heterogeneity; do not target a rollout from subgroup p-values alone. The table includes Benjamini–Hochberg q-values.")
    dimension = st.selectbox("Segment dimension", ["device", "acquisition_channel", "region", "customer_tenure"],
                             format_func=lambda x: x.replace("_", " ").title())
    subset = r["segments"].query("segment == @dimension").sort_values("effect")
    fig = go.Figure()
    fig.add_vline(x=0, line_color=MUTED, line_dash="dash")
    fig.add_trace(go.Scatter(x=subset.effect*100, y=subset.level, mode="markers",
                             marker=dict(size=13, color=MINT),
                             error_x=dict(type="data", symmetric=False,
                                          array=(subset.ci_high-subset.effect)*100,
                                          arrayminus=(subset.effect-subset.ci_low)*100,
                                          color=MINT, thickness=2), showlegend=False,
                             customdata=subset[["n", "q_value_bh"]],
                             hovertemplate="%{y}<br>Lift: %{x:+.2f} pp<br>N: %{customdata[0]:,}"
                                           "<br>BH q-value: %{customdata[1]:.3f}<extra></extra>"))
    fig.update_xaxes(title="Treatment minus control conversion (percentage points)")
    base_chart(fig, 320)
    display = subset[["level", "n", "control_rate", "treatment_rate", "effect", "p_value", "q_value_bh"]].copy()
    for col in ["control_rate", "treatment_rate"]: display[col] = display[col].map(lambda x: f"{x:.2%}")
    display["effect"] = display.effect.map(pp)
    for col in ["p_value", "q_value_bh"]: display[col] = display[col].map(lambda x: f"{x:.3g}")
    st.dataframe(display, hide_index=True, width="stretch")

    st.markdown("#### Assignment cohorts")
    cohorts = df.groupby(["assigned_at", "variant"]).paid_14d.agg(["mean", "size"]).reset_index()
    fig = go.Figure()
    for variant, color in [("control", BLUE), ("treatment", MINT)]:
        part = cohorts[cohorts.variant == variant]
        fig.add_trace(go.Scatter(x=part.assigned_at, y=part["mean"]*100,
                                 mode="lines+markers", name=variant.title(),
                                 line=dict(color=color, width=2)))
    fig.update_xaxes(title="Assignment date")
    fig.update_yaxes(title="14-day paid conversion (%)")
    base_chart(fig, 300)

with decision:
    st.subheader("Decision framework")
    st.markdown("Predeclared rule: ship only if the primary lift is positive and significant at 5%, "
                "SRM p ≥ 0.001, maximum baseline |SMD| < 0.10, and both guardrail upper 95% "
                "confidence bounds are below their maximum acceptable increases.")
    checks = pd.DataFrame([
        ["Primary paid conversion", f"{pp(p.effect)} · p={p.p_value:.3g}", "Pass" if p.effect > 0 and p.p_value < .05 else "Fail"],
        ["Assignment integrity", f"SRM p={r['srm']['p_value']:.3f}", "Pass" if r['srm']['pass'] else "Fail"],
        ["Pre-treatment balance", f"max |SMD|={r['balance'].smd.abs().max():.3f}", "Pass" if r['balance_pass'] else "Fail"],
        *[[k.replace("_", " ").title(),
           f"upper CI {v.ci_high*100:+.2f} pp vs margin {GUARDRAILS[k]*100:.2f} pp",
           "Pass" if r["guardrail_pass"][k] else "Fail"] for k, v in r["guardrails"].items()],
    ], columns=["Gate", "Observed", "Status"])
    st.dataframe(checks, hide_index=True, width="stretch")
    st.markdown('<div class="callout"><strong>Recommendation: HOLD.</strong> Instrument and reproduce the '
                'crash increase by device and app version. Fix the issue, then run a new, powered confirmation test. '
                'Do not declare a win from conversion alone.</div>', unsafe_allow_html=True)
    st.markdown("#### Business impact scenario")
    users = st.slider("Eligible users per month", min_value=10_000, max_value=200_000,
                      value=50_000, step=5_000)
    monthly = users * p.effect
    revenue_per_payer = df.revenue_usd_14d.sum() / df.paid_14d.sum()
    a, b, c = st.columns(3)
    a.metric("Incremental payers / month", f"{monthly:,.0f}")
    b.metric("Gross 14-day revenue / month", f"${monthly*revenue_per_payer:,.0f}")
    c.metric("Potential extra crashes / month", f"{users*r['guardrails']['app_crash_14d'].effect:,.0f}")
    st.caption("Illustrative extrapolation from the observed synthetic experiment; assumes comparable traffic "
               "and payer value. It is not a forecast or a substitute for a safety review.")

with methods:
    st.subheader("Design and statistical notes")
    st.markdown("""
**Hypothesis.** Guided onboarding raises the share of assigned eligible users who pay within 14 days.

**Estimand.** Intent-to-treat absolute difference in paid conversion (treatment minus control). Unit of randomization and analysis: user. Each user appears once. Enrollment was fixed to February 1–14, 2025; follow-up was complete by March 1. No peeking or early stop is modeled.

**Inference.** Primary: two-sided pooled two-proportion z test at α = 0.05; 95% difference interval from Newcombe's hybrid Wilson method. Revenue per assigned user: large-sample unequal-variance normal interval and test. SRM: chi-square goodness-of-fit against 50/50. Baseline balance: standardized mean differences for categorical indicators. Assumptions include independent user assignments and complete outcomes.

**Multiplicity.** Only paid conversion is confirmatory. Secondary activation, revenue, and guardrail difference p-values receive Holm adjustment as descriptive diagnostics. Segment tests receive Benjamini–Hochberg adjustment; they remain exploratory. Guardrails are judged with prespecified absolute harm margins and the upper end of two-sided 95% intervals, not by a nonsignificant harm p-value.

**Limitations.** Data are synthetic; the result is an analytical demonstration rather than a real business experiment. Revenue is measured over only 14 days and omits acquisition costs, retention, refunds, and support cost. No cross-device identity issues, network effects, missingness, or sequential monitoring are simulated.
""")
    a, b, c = st.columns(3)
    a.metric("80% power MDE", pp(r["mde"]))
    b.metric("Power for +1.0 pp", f"{r['power_for_1pp']:.1%}")
    c.metric("Primary p-value", f"{p.p_value:.3g}")
    st.caption("MDE and power use a two-sided normal approximation and the smaller realized arm size. "
               "The MDE is a design diagnostic, not a post hoc claim of achieved power.")
