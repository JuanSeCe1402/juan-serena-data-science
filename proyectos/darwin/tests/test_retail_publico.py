import pandas as pd
import pytest
from retail_publico import clean_transactions, snapshot


def rows():
    return pd.DataFrame([
        ["A", "SKU", 1, "2011-02-28", 10, 1],
        ["B", "SKU", 1, "2011-02-28", 20, 2],
        ["F", "SKU", 1, "2011-03-01", 999, 1],
        ["D", "SKU", 1, "2011-03-31", 500, 2],
        ["E", "SKU", 1, "2011-03-10", 900, 3],
    ], columns=["Invoice", "StockCode", "Quantity", "InvoiceDate", "Price", "Customer ID"])


def test_cutoffs_exclude_future_features_and_future_only_customers():
    clean, _ = clean_transactions(rows())
    frame = snapshot(clean, "2011-03-01")
    assert list(frame.index) == [1, 2]
    assert frame.spend_gbp.tolist() == [10, 20]
    assert frame.repurchased.tolist() == [1, 0]  # March 31 is exactly outside the 30-day horizon.
    altered = clean.copy()
    altered.loc[altered.InvoiceDate >= "2011-03-01", "amount"] = 1e12
    pd.testing.assert_frame_equal(frame, snapshot(altered, "2011-03-01"))


@pytest.mark.parametrize("cutoff", ["2010-01-01", "2011-11-20"])
def test_incomplete_windows_rejected(cutoff):
    clean, _ = clean_transactions(rows())
    with pytest.raises(ValueError, match="completamente"):
        snapshot(clean, cutoff)


def test_cleaning_cancellations_missing_duplicates_and_zero_price():
    raw = rows()
    raw = pd.concat([raw, raw.iloc[[0]]], ignore_index=True)
    raw.loc[1, "Invoice"] = "c123"
    raw.loc[2, "Customer ID"] = None
    raw.loc[3, "Price"] = 0
    clean, counts = clean_transactions(raw)
    assert len(clean) == 2
    assert counts["missing_or_invalid_removed"] == 1
    assert counts["cancellations_nonpositive_removed"] == 2
    assert counts["duplicate_lines_removed"] == 1
