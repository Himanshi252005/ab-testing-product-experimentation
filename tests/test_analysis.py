import sqlite3

import pandas as pd
import pytest

from src.analysis import (analyze, bh_adjust, binary_test, holm_adjust,
                          sample_ratio_mismatch, validate_data)
from src.generate_data import generate


@pytest.fixture(scope="module")
def data():
    return generate()


def test_generator_is_deterministic_and_one_row_per_user(data):
    pd.testing.assert_frame_equal(data, generate())
    assert len(data) == 40_000
    assert data.user_id.is_unique
    assert (data.loc[data.paid_14d == 0, "revenue_usd_14d"] == 0).all()
    validate_data(data)


def test_primary_effect_matches_direct_group_calculation(data):
    result = binary_test(data, "paid_14d")
    means = data.groupby("variant").paid_14d.mean()
    assert result.effect == pytest.approx(means["treatment"] - means["control"])
    assert result.ci_low < result.effect < result.ci_high
    assert 0 <= result.p_value <= 1


def test_integrity_and_decision_gates(data):
    result = analyze(data)
    assert result["srm"]["pass"]
    assert result["balance_pass"]
    assert result["primary"].p_value < .05
    assert result["guardrail_pass"]["app_crash_14d"] is False
    assert result["ship_recommended"] is False
    assert .008 < result["mde"] < .011


def test_srm_detects_large_allocation_error(data):
    skewed = pd.concat([data[data.variant == "control"].head(100),
                        data[data.variant == "treatment"].head(900)])
    assert sample_ratio_mismatch(skewed)["p_value"] < .001


def test_multiplicity_adjustments_are_monotone_and_bounded():
    holm = holm_adjust({"a": .01, "b": .04, "c": .20})
    assert holm == pytest.approx({"a": .03, "b": .08, "c": .20})
    bh = bh_adjust([.01, .04, .20])
    assert bh == pytest.approx([.03, .06, .20])


def test_sql_conversion_agrees_with_python(data):
    with sqlite3.connect(":memory:") as con:
        data.to_sql("experiment_users", con, index=False)
        rows = pd.read_sql_query(
            "SELECT variant, COUNT(*) n, SUM(paid_14d) paid "
            "FROM experiment_users GROUP BY variant", con).set_index("variant")
    result = binary_test(data, "paid_14d")
    assert rows.loc["control", "n"] == result.control_n
    assert rows.loc["treatment", "paid"] / rows.loc["treatment", "n"] == pytest.approx(result.treatment_rate)


def test_invalid_data_is_rejected(data):
    duplicate = pd.concat([data, data.iloc[[0]]])
    with pytest.raises(ValueError, match="unique"):
        validate_data(duplicate)
