"""
risk_utils.py
=============
Utility functions for financial risk calculations (VaR, CVaR, HHI).
"""

import numpy as np
import pandas as pd

def calculate_var_95(returns: pd.Series) -> float:
    """
    Calculate the 95% Value at Risk (VaR) for a series of returns.
    This represents the 5th percentile of the returns distribution.
    """
    if returns.empty:
        return 0.0
    return float(np.percentile(returns.dropna(), 5))

def calculate_cvar_95(returns: pd.Series, var_95: float = None) -> float:
    """
    Calculate the 95% Conditional Value at Risk (CVaR).
    This represents the average return of the worst 5% cases (returns below VaR).
    """
    clean_returns = returns.dropna()
    if clean_returns.empty:
        return 0.0
    if var_95 is None:
        var_95 = calculate_var_95(clean_returns)
    
    tail = clean_returns[clean_returns <= var_95]
    if tail.empty:
        return var_95
    return float(tail.mean())

def calculate_hhi(weights_pct: pd.Series) -> float:
    """
    Calculate the Herfindahl-Hirschman Index (HHI) for portfolio concentration.
    Expects weights as percentage values (0 to 100).
    """
    clean_weights = weights_pct.dropna()
    if clean_weights.empty:
        return 0.0
    # Convert weights to decimals and sum their squares
    weights_dec = clean_weights / 100.0
    return float((weights_dec ** 2).sum())
