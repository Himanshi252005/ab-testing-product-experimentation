"""Generate explicitly synthetic, deterministic user-level experiment data."""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "experiment_users.csv"
N_USERS = 40_000
SEED = 20250201


def generate(n_users: int = N_USERS, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    # Randomization is independent of all pre-treatment attributes.
    variant = rng.choice(["control", "treatment"], size=n_users)
    assignment_day = rng.integers(0, 14, size=n_users)
    device = rng.choice(["desktop", "mobile", "tablet"], n_users, p=[.42, .52, .06])
    channel = rng.choice(["organic", "paid", "referral"], n_users, p=[.48, .37, .15])
    region = rng.choice(["North America", "Europe", "Other"], n_users, p=[.47, .34, .19])
    tenure = rng.choice(["new", "returning"], n_users, p=[.62, .38])
    treatment = variant == "treatment"

    # Plausible heterogeneous baseline risk. The experiment improves onboarding.
    baseline = (
        .105
        + np.where(device == "desktop", .013, 0)
        + np.where(device == "tablet", -.013, 0)
        + np.where(channel == "referral", .012, 0)
        + np.where(channel == "paid", -.009, 0)
        + np.where(region == "North America", .007, 0)
        + np.where(tenure == "returning", .020, 0)
    )
    paid = rng.binomial(1, np.clip(baseline + treatment * .014, 0, 1))
    activation_p = .34 + .025 * treatment + .03 * (tenure == "returning")
    activated = np.maximum(paid, rng.binomial(1, activation_p))
    support_p = .039 + .001 * treatment + .006 * (device == "mobile")
    crash_p = .019 + .0005 * treatment + .004 * (device == "mobile")
    support = rng.binomial(1, support_p)
    crash = rng.binomial(1, crash_p)
    # Positive spend only for paid converters; all other users have zero revenue.
    spend = np.round(rng.lognormal(np.log(45), .43, n_users), 2)
    revenue = np.where(paid == 1, spend, 0.0)

    return pd.DataFrame({
        "user_id": [f"U{i:06d}" for i in range(1, n_users + 1)],
        "assigned_at": (pd.Timestamp("2025-02-01") + pd.to_timedelta(assignment_day, unit="D")).strftime("%Y-%m-%d"),
        "variant": variant,
        "device": device,
        "acquisition_channel": channel,
        "region": region,
        "customer_tenure": tenure,
        "activated_7d": activated.astype(int),
        "paid_14d": paid.astype(int),
        "revenue_usd_14d": revenue,
        "support_ticket_14d": support.astype(int),
        "app_crash_14d": crash.astype(int),
    })


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frame = generate()
    frame.to_csv(OUTPUT, index=False)
    print(f"Wrote {len(frame):,} synthetic users to {OUTPUT}")
