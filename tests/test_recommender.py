import pytest
import pandas as pd
from unittest.mock import patch
from recommender import recommend

# Dummy performance data for testing
DUMMY_PERF = pd.DataFrame({
    "scheme_name": ["Fund A", "Fund B", "Fund C"],
    "fund_house": ["House X", "House Y", "House Z"],
    "category": ["Debt", "Equity", "Hybrid"],
    "sharpe_ratio": [1.5, 2.0, 1.2],
    "return_3yr_pct": [12.0, 15.0, 10.0],
    "std_dev_ann_pct": [8.0, 12.0, 10.0],
    "expense_ratio_pct": [1.0, 1.5, 1.2],
    "risk_grade": ["Low", "High", "Moderate"]
})

@patch("recommender.pd.read_csv")
def test_recommend_low_risk(mock_read_csv):
    mock_read_csv.return_value = DUMMY_PERF
    
    result = recommend("Low", top_n=1)
    
    assert len(result) == 1
    assert result.iloc[0]["scheme_name"] == "Fund A"
    assert result.iloc[0]["risk_grade"] == "Low"

@patch("recommender.pd.read_csv")
def test_recommend_invalid_risk(mock_read_csv):
    mock_read_csv.return_value = DUMMY_PERF
    
    with pytest.raises(ValueError):
        recommend("Ultra-High")
