# Predeclared experiment plan

**Product change:** guided onboarding replaces the current first run flow. **Population:** eligible SaaS users enrolled February 1–14, 2025. **Randomization:** independent 50/50 user-level assignment. **Analysis:** one readout on March 1 after every user's 14-day window closes. This plan is part of a synthetic portfolio simulation; it was authored alongside the generator and is not evidence of a real preregistration.

## Metrics and hypotheses

| Role | Metric | Hypothesis or margin |
| --- | --- | --- |
| Primary | Paid conversion by day 14 | Treatment > control; tested two-sided at 5% with positive observed effect required. |
| Secondary | Activation by day 7 | Diagnostic only. |
| Secondary | Revenue per assigned user by day 14 | Diagnostic only; includes zeros. |
| Guardrail | Support ticket user rate by day 14 | Upper 95% CI of treatment-control difference ≤ +0.6 percentage points. |
| Guardrail | App crash user rate by day 14 | Upper 95% CI of treatment-control difference ≤ +0.5 percentage points. |

## Decision gates

Recommend ship only if all hold: primary positive with p < 0.05; SRM p ≥ 0.001 against 50/50; maximum baseline categorical |SMD| < 0.10; both guardrail upper confidence bounds below their harm margins. Guardrail bounds use two-sided 95% Newcombe–Wilson intervals. Segment findings do not change the launch decision.

## Power planning

At the realized control baseline and smaller arm size, the normal approximation yields an 80% power MDE near 0.93 percentage points. The experiment was sized at 40,000 assigned users to detect a roughly 1 percentage point absolute lift. This is a design approximation; actual data collection in a company would use an ex ante baseline estimate, traffic forecast, and agreed practical effect.

## Threats to validity

Check user identity and exposure logging, repeat assignments, outcome maturity, missing events, instrumentation by variant, cross-device attribution, and simultaneous campaigns before a real decision. This simulation assumes those operational issues are absent.
