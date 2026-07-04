# backend/app/analytics/engine.py
import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import List, Dict, Any

def calculate_returns(prices: pd.Series) -> pd.Series:
    """Calculate daily returns from price series."""
    return prices.pct_change().dropna()

def calculate_cagr(initial_val: float, final_val: float, num_days: int) -> float:
    """Calculate Compound Annual Growth Rate (CAGR) based on calendar days (365-day year)."""
    if initial_val <= 0 or final_val <= 0 or num_days <= 0:
        return 0.0
    years = num_days / 365.25
    return float((final_val / initial_val) ** (1.0 / years) - 1.0) * 100.0

def calculate_volatility(daily_returns: pd.Series, periods: int = 252) -> float:
    """Calculate annualized standard deviation (volatility)."""
    if len(daily_returns) < 2:
        return 0.0
    return float(daily_returns.std() * np.sqrt(periods)) * 100.0

def calculate_downside_deviation(daily_returns: pd.Series, target_return: float = 0.0, periods: int = 252) -> float:
    """Calculate annualized downside deviation (used for Sortino ratio)."""
    if len(daily_returns) < 2:
        return 0.0
    downside_diff = daily_returns - target_return
    downside_diff = downside_diff.clip(upper=0.0)  # keep negative differences only
    return float(np.sqrt(np.mean(downside_diff ** 2)) * np.sqrt(periods)) * 100.0

def calculate_sharpe_ratio(cagr: float, risk_free_rate: float, volatility: float) -> float:
    """Calculate Sharpe ratio: (CAGR - Rf) / Volatility."""
    if volatility <= 0:
        return 0.0
    return (cagr - risk_free_rate) / volatility

def calculate_sortino_ratio(cagr: float, risk_free_rate: float, downside_dev: float) -> float:
    """Calculate Sortino ratio: (CAGR - Rf) / Downside Volatility."""
    if downside_dev <= 0:
        return 0.0
    return (cagr - risk_free_rate) / downside_dev

def calculate_treynor_ratio(cagr: float, risk_free_rate: float, beta: float) -> float:
    """Calculate Treynor ratio: (CAGR - Rf) / Beta."""
    if beta == 0:
        return 0.0
    return (cagr - risk_free_rate) / beta

def calculate_max_drawdown(prices: pd.Series) -> float:
    """Calculate maximum peak-to-trough historical drawdown."""
    if len(prices) < 2:
        return 0.0
    roll_max = prices.cummax()
    drawdown = (prices - roll_max) / roll_max
    return float(drawdown.min()) * 100.0

def calculate_calmar_ratio(cagr: float, max_drawdown: float) -> float:
    """Calculate Calmar ratio: CAGR / |Max Drawdown|."""
    abs_dd = abs(max_drawdown)
    if abs_dd <= 0:
        return 0.0
    return cagr / abs_dd

def calculate_var_95(daily_returns: pd.Series) -> float:
    """Calculate historical Value at Risk at 95% confidence level."""
    if len(daily_returns) == 0:
        return 0.0
    return float(np.percentile(daily_returns, 5)) * 100.0

def calculate_cvar_95(daily_returns: pd.Series, var_95: float = None) -> float:
    """Calculate 95% Conditional Value at Risk (Expected Shortfall)."""
    if len(daily_returns) == 0:
        return 0.0
    if var_95 is None:
        var_95 = np.percentile(daily_returns, 5)
    else:
        var_95 = var_95 / 100.0  # Convert back to decimal if passed in %
    tail = daily_returns[daily_returns <= var_95]
    if len(tail) == 0:
        return float(var_95) * 100.0
    return float(tail.mean()) * 100.0

def calculate_beta(fund_returns: pd.Series, bench_returns: pd.Series) -> float:
    """Calculate Beta via covariance dividing by benchmark variance."""
    # Align the returns on dates
    df = pd.concat([fund_returns, bench_returns], axis=1).dropna()
    if len(df) < 5:
        return 1.0
    cov = df.cov().iloc[0, 1]
    bench_var = df.iloc[:, 1].var()
    if bench_var == 0:
        return 1.0
    return float(cov / bench_var)

def calculate_alpha(cagr: float, risk_free_rate: float, beta: float, bench_cagr: float) -> float:
    """Calculate Jensen's Alpha: CAGR - [Rf + Beta * (Bench_CAGR - Rf)]."""
    return cagr - (risk_free_rate + beta * (bench_cagr - risk_free_rate))

def calculate_tracking_error(fund_returns: pd.Series, bench_returns: pd.Series, periods: int = 252) -> float:
    """Calculate Tracking Error (annualized standard deviation of active returns)."""
    df = pd.concat([fund_returns, bench_returns], axis=1).dropna()
    if len(df) < 2:
        return 0.0
    active_return = df.iloc[:, 0] - df.iloc[:, 1]
    return float(active_return.std() * np.sqrt(periods)) * 100.0

def calculate_information_ratio(cagr: float, bench_cagr: float, tracking_error: float) -> float:
    """Calculate Information Ratio: (CAGR - Bench_CAGR) / Tracking Error."""
    if tracking_error <= 0:
        return 0.0
    return (cagr - bench_cagr) / tracking_error

def calculate_hhi(weights_pct: List[float]) -> float:
    """Calculate Herfindahl-Hirschman Index (HHI) for weight concentration."""
    if not weights_pct:
        return 0.0
    weights_dec = [w / 100.0 for w in weights_pct]
    return float(sum(w ** 2 for w in weights_dec))
