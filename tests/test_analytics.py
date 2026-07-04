import pytest
import pandas as pd
import numpy as np
from risk_utils import calculate_var_95, calculate_cvar_95, calculate_hhi

def test_calculate_var_95():
    # Simple array: 1 to 20
    returns = pd.Series(np.linspace(-0.10, 0.10, 20))
    # 5th percentile of 20 points
    var_val = calculate_var_95(returns)
    
    assert isinstance(var_val, float)
    assert var_val < 0.0 # Loss tail

def test_calculate_cvar_95():
    returns = pd.Series([-0.05, -0.04, -0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03, 0.04])
    var_95 = calculate_var_95(returns)
    cvar_95 = calculate_cvar_95(returns, var_95)
    
    assert isinstance(cvar_95, float)
    assert cvar_95 <= var_95

def test_calculate_hhi():
    # Equal weights: 4 stocks, 25% each
    weights = pd.Series([25.0, 25.0, 25.0, 25.0])
    hhi = calculate_hhi(weights)
    
    # 4 * (0.25^2) = 4 * 0.0625 = 0.25
    assert pytest.approx(hhi) == 0.25

    # Empty weights
    assert calculate_hhi(pd.Series([])) == 0.0
