"""Frequentist intent-to-treat analysis with explicit decision criteria."""

from dataclasses import asdict, dataclass
from math import erfc, sqrt
from statistics import NormalDist

import numpy as np
import pandas as pd

NORMAL = NormalDist()


def normal_sf(value: float) -> float:
    return .5 * erfc(value / sqrt(2))

PRIMARY = "paid_14d"
SECONDARY = "activated_7d"
GUARDRAILS = {"support_ticket_14d": .006, "app_crash_14d": .005}
ALPHA = .05


@dataclass
class BinaryResult:
    metric: str
    control_n: int
    treatment_n: int
    control_rate: float
    treatment_rate: float
    effect: float
    relative_lift: float
    ci_low: float
    ci_high: float
    p_value: float

    def to_dict(self):
        return asdict(self)


def validate_data(df: pd.DataFrame) -> None:
    required = {
        "user_id", "assigned_at", "variant", "device", "acquisition_channel",
        "region", "customer_tenure", "paid_14d", "activated_7d",
        "revenue_usd_14d", "support_ticket_14d", "app_crash_14d",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if df.empty or df.user_id.isna().any() or df.user_id.duplicated().any():
        raise ValueError("Expected one non-null row per unique assigned user")
    if set(df.variant) != {"control", "treatment"}:
        raise ValueError("Expected both control and treatment variants only")
    for metric in [PRIMARY, SECONDARY, *GUARDRAILS]:
        if df[metric].isna().any() or not df[metric].isin([0, 1]).all():
            raise ValueError(f"{metric} must be a complete binary outcome")
    revenue = pd.to_numeric(df.revenue_usd_14d, errors="coerce")
    if revenue.isna().any() or (revenue < 0).any():
        raise ValueError("Revenue must be nonnegative and complete")
    if (revenue[df.paid_14d == 0] != 0).any():
        raise ValueError("Non-converters must have zero revenue")
    dates = pd.to_datetime(df.assigned_at, errors="coerce")
    if dates.isna().any():
        raise ValueError("Invalid assignment date")


def sample_ratio_mismatch(df: pd.DataFrame, expected_treatment_share=.5) -> dict:
    n_t = int((df.variant == "treatment").sum())
    n_c = int((df.variant == "control").sum())
    n = n_t + n_c
    chi2 = (n_t - n * expected_treatment_share) ** 2 / (n * expected_treatment_share)
    chi2 += (n_c - n * (1 - expected_treatment_share)) ** 2 / (n * (1 - expected_treatment_share))
    return {"control_n": n_c, "treatment_n": n_t, "treatment_share": n_t / n,
            "chi2": float(chi2), "p_value": erfc(sqrt(chi2 / 2)),
            "pass": bool(erfc(sqrt(chi2 / 2)) >= .001)}


def randomization_balance(df: pd.DataFrame) -> pd.DataFrame:
    """Categorical level differences, normalized using pooled Bernoulli SD."""
    records = []
    for column in ["device", "acquisition_channel", "region", "customer_tenure", "assigned_at"]:
        for level in sorted(df[column].unique()):
            c = float((df.loc[df.variant == "control", column] == level).mean())
            t = float((df.loc[df.variant == "treatment", column] == level).mean())
            pooled = (c + t) / 2
            denom = sqrt(pooled * (1 - pooled))
            smd = (t - c) / denom if denom else 0.0
            records.append({"attribute": column, "level": str(level), "control_share": c,
                            "treatment_share": t, "smd": smd})
    return pd.DataFrame(records)


def _wilson(successes: int, n: int, alpha=ALPHA) -> tuple[float, float]:
    z = NORMAL.inv_cdf(1 - alpha / 2)
    p = successes / n
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return center - half, center + half


def binary_test(df: pd.DataFrame, metric: str, alpha=ALPHA) -> BinaryResult:
    c = df.loc[df.variant == "control", metric]
    t = df.loc[df.variant == "treatment", metric]
    nc, nt = len(c), len(t)
    if not nc or not nt:
        raise ValueError("Both variants need observations")
    xc, xt = int(c.sum()), int(t.sum())
    pc, pt = xc / nc, xt / nt
    pooled = (xc + xt) / (nc + nt)
    se_null = sqrt(pooled * (1 - pooled) * (1 / nc + 1 / nt))
    p_value = float(2 * normal_sf(abs((pt - pc) / se_null))) if se_null else 1.0
    # Newcombe's hybrid Wilson interval for an unpaired difference in proportions.
    lc, uc = _wilson(xc, nc, alpha)
    lt, ut = _wilson(xt, nt, alpha)
    effect = pt - pc
    lower = effect - sqrt((pt - lt) ** 2 + (uc - pc) ** 2)
    upper = effect + sqrt((ut - pt) ** 2 + (pc - lc) ** 2)
    return BinaryResult(metric, nc, nt, pc, pt, effect,
                        effect / pc if pc else float("nan"), lower, upper, p_value)


def revenue_test(df: pd.DataFrame, alpha=ALPHA) -> dict:
    c = df.loc[df.variant == "control", "revenue_usd_14d"].to_numpy(dtype=float)
    t = df.loc[df.variant == "treatment", "revenue_usd_14d"].to_numpy(dtype=float)
    diff = float(t.mean() - c.mean())
    vc, vt = c.var(ddof=1), t.var(ddof=1)
    se = sqrt(vc / len(c) + vt / len(t))
    # Large-sample normal approximation for mean revenue per assigned user.
    # Zero-revenue users remain in the denominator (intent to treat).
    critical = NORMAL.inv_cdf(1 - alpha / 2)
    return {"control_mean": float(c.mean()), "treatment_mean": float(t.mean()),
            "effect": diff, "ci_low": float(diff - critical * se),
            "ci_high": float(diff + critical * se),
            "p_value": float(2 * normal_sf(abs(diff / se))) if se else 1.0}


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(p_values, key=p_values.get)
    m = len(ordered)
    adjusted, running = {}, 0.0
    for rank, key in enumerate(ordered):
        running = max(running, min(1.0, (m - rank) * p_values[key]))
        adjusted[key] = running
    return adjusted


def bh_adjust(p_values: list[float]) -> list[float]:
    values = np.asarray(p_values, dtype=float)
    order = np.argsort(values)
    result = np.empty(len(values))
    running = 1.0
    for rank in range(len(values) - 1, -1, -1):
        idx = order[rank]
        running = min(running, values[idx] * len(values) / (rank + 1))
        result[idx] = running
    return result.tolist()


def power_at_effect(p0: float, absolute_effect: float, n_per_arm: int, alpha=ALPHA) -> float:
    """Normal-approximation two-sided power for two independent proportions."""
    p1 = p0 + absolute_effect
    if not 0 < p0 < 1 or not 0 < p1 < 1 or n_per_arm <= 0:
        raise ValueError("Invalid baseline, effect, or sample size")
    pooled = (p0 + p1) / 2
    se_null = sqrt(2 * pooled * (1 - pooled) / n_per_arm)
    se_alt = sqrt((p0 * (1 - p0) + p1 * (1 - p1)) / n_per_arm)
    threshold = NORMAL.inv_cdf(1 - alpha / 2) * se_null
    return float(normal_sf((threshold - absolute_effect) / se_alt)
                 + NORMAL.cdf((-threshold - absolute_effect) / se_alt))


def minimum_detectable_effect(p0: float, n_per_arm: int, target_power=.8) -> float:
    lo, hi = 1e-8, min(.5, 1 - p0 - 1e-8)
    for _ in range(60):
        mid = (lo + hi) / 2
        if power_at_effect(p0, mid, n_per_arm) < target_power:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def segment_results(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for column in ["device", "acquisition_channel", "region", "customer_tenure"]:
        for level, subset in df.groupby(column):
            result = binary_test(subset, PRIMARY)
            records.append({"segment": column, "level": level,
                            "n": len(subset), "control_rate": result.control_rate,
                            "treatment_rate": result.treatment_rate, "effect": result.effect,
                            "ci_low": result.ci_low, "ci_high": result.ci_high,
                            "p_value": result.p_value})
    out = pd.DataFrame(records)
    out["q_value_bh"] = bh_adjust(out.p_value.tolist())
    return out


def analyze(df: pd.DataFrame) -> dict:
    validate_data(df)
    srm = sample_ratio_mismatch(df)
    balance = randomization_balance(df)
    primary = binary_test(df, PRIMARY)
    secondary = binary_test(df, SECONDARY)
    guardrails = {metric: binary_test(df, metric) for metric in GUARDRAILS}
    revenue = revenue_test(df)
    adjusted = holm_adjust({SECONDARY: secondary.p_value,
                            "revenue_usd_14d": revenue["p_value"],
                            **{k: v.p_value for k, v in guardrails.items()}})
    # A guardrail passes only if its 95% two-sided upper bound excludes the
    # predeclared maximum acceptable absolute increase.
    guardrail_pass = {k: v.ci_high <= GUARDRAILS[k] for k, v in guardrails.items()}
    balanced = bool(balance.smd.abs().max() < .1)
    decision = bool(srm["pass"] and balanced and primary.p_value < ALPHA
                    and primary.effect > 0 and all(guardrail_pass.values()))
    n_arm = min(srm["control_n"], srm["treatment_n"])
    return {"srm": srm, "balance": balance, "balance_pass": balanced,
            "primary": primary, "secondary": secondary, "guardrails": guardrails,
            "guardrail_pass": guardrail_pass, "revenue": revenue,
            "adjusted_p": adjusted, "segments": segment_results(df),
            "mde": minimum_detectable_effect(primary.control_rate, n_arm),
            "power_for_1pp": power_at_effect(primary.control_rate, .01, n_arm),
            "ship_recommended": decision}
