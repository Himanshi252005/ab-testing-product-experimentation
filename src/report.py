"""Print a reproducible, concise experiment readout."""

from pathlib import Path
import pandas as pd

from .analysis import analyze

ROOT = Path(__file__).resolve().parents[1]


def main():
    result = analyze(pd.read_csv(ROOT / "data" / "experiment_users.csv"))
    p = result["primary"]
    print("EXPERIMENT READOUT - SYNTHETIC DATA")
    print(f"Assigned: {p.control_n:,} control / {p.treatment_n:,} treatment")
    print(f"SRM p={result['srm']['p_value']:.4f}; max |SMD|={result['balance'].smd.abs().max():.3f}")
    print(f"Paid conversion: {p.control_rate:.2%} to {p.treatment_rate:.2%}")
    print(f"Absolute lift: {p.effect*100:+.2f} pp (95% CI {p.ci_low*100:+.2f} to {p.ci_high*100:+.2f}); p={p.p_value:.3g}")
    print(f"MDE at 80% power: {result['mde']*100:.2f} pp")
    for metric, guard in result["guardrails"].items():
        print(f"{metric}: change {guard.effect*100:+.2f} pp; 95% upper {guard.ci_high*100:+.2f} pp; pass={result['guardrail_pass'][metric]}")
    print("Decision:", "SHIP" if result["ship_recommended"] else "HOLD / INVESTIGATE")


if __name__ == "__main__":
    main()
