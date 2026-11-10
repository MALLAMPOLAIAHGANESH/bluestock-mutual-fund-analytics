# backend/app/machine_learning/engine.py
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.cluster import KMeans
from typing import List, Dict, Any, Tuple

# --- 1. Monte Carlo Simulation (Geometric Brownian Motion) ---
def run_monte_carlo(
    initial_nav: float,
    annual_return: float,
    annual_volatility: float,
    num_years: int = 5,
    num_simulations: int = 10000
) -> np.ndarray:
    """
    Run Monte Carlo simulation using Geometric Brownian Motion.
    Returns simulated NAV prices paths: shape (steps, simulations)
    """
    # Annualized parameters to daily parameters
    trading_days = 252
    steps = num_years * trading_days
    dt = 1.0 / trading_days
    
    # CAGR and Vol to decimals
    mu = annual_return / 100.0
    sigma = annual_volatility / 100.0
    
    # Drift and diffusion terms
    drift = (mu - 0.5 * sigma ** 2) * dt
    diffusion = sigma * np.sqrt(dt)
    
    # Simulate daily shocks
    shocks = np.random.normal(0, 1, size=(steps, num_simulations))
    daily_growth = np.exp(drift + diffusion * shocks)
    
    # Accumulate prices
    nav_paths = np.zeros((steps + 1, num_simulations))
    nav_paths[0, :] = initial_nav
    
    for t in range(1, steps + 1):
        nav_paths[t, :] = nav_paths[t - 1, :] * daily_growth[t - 1, :]
        
    return nav_paths

# --- 2. Markowitz Efficient Frontier Optimization ---
def portfolio_performance(weights: np.ndarray, mean_returns: np.ndarray, cov_matrix: np.ndarray) -> Tuple[float, float]:
    """Calculate expected return and expected volatility for portfolio weights."""
    p_return = np.sum(mean_returns * weights) * 252
    p_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix * 252, weights)))
    return p_return, p_volatility

def negative_sharpe_ratio(weights: np.ndarray, mean_returns: np.ndarray, cov_matrix: np.ndarray, risk_free_rate: float) -> float:
    """Calculate negative Sharpe ratio for minimization."""
    p_return, p_volatility = portfolio_performance(weights, mean_returns, cov_matrix)
    if p_volatility <= 0:
        return 0.0
    return -(p_return - risk_free_rate) / p_volatility

def optimize_portfolio(
    daily_returns_df: pd.DataFrame,
    risk_free_rate: float = 6.5
) -> Tuple[np.ndarray, float, float, float]:
    """
    Optimize portfolio weights to maximize Sharpe Ratio using Markowitz Frontier.
    
    Returns
    -------
    Optimal Weights (array), Expected Return (%), Expected Volatility (%), Sharpe Ratio
    """
    num_assets = len(daily_returns_df.columns)
    mean_returns = daily_returns_df.mean().values
    cov_matrix = daily_returns_df.cov().values
    
    # Initial weights: equal division
    initial_weights = np.ones(num_assets) / num_assets
    
    # Constraints: weights sum to 1.0
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})
    
    # Bounds: no shorting (weights between 0 and 1)
    bounds = tuple((0.0, 1.0) for _ in range(num_assets))
    
    # Convert risk free rate to decimal
    rf_dec = risk_free_rate / 100.0
    
    result = minimize(
        negative_sharpe_ratio,
        initial_weights,
        args=(mean_returns, cov_matrix, rf_dec),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )
    
    opt_weights = result.x
    opt_return, opt_vol = portfolio_performance(opt_weights, mean_returns, cov_matrix)
    
    # Convert back to percentages
    opt_return_pct = opt_return * 100.0
    opt_vol_pct = opt_vol * 100.0
    sharpe = (opt_return_pct - risk_free_rate) / opt_vol_pct if opt_vol_pct > 0 else 0.0
    
    return opt_weights, opt_return_pct, opt_vol_pct, sharpe

# --- 3. Risk Classification Using K-Means Clustering ---
def classify_fund_risks(volatilities: List[float], drawdowns: List[float]) -> List[str]:
    """
    Classify funds into risk tiers (Low, Moderate, High, Very High) using K-Means Clustering.
    """
    if len(volatilities) < 4:
        # Fallback to simple rule-based classification if too few funds
        classes = []
        for vol in volatilities:
            if vol < 8.0: classes.append("Low")
            elif vol < 15.0: classes.append("Moderate")
            elif vol < 22.0: classes.append("High")
            else: classes.append("Very High")
        return classes

    df = pd.DataFrame({"vol": volatilities, "dd": drawdowns})
    
    # Normalize features
    normalized_df = (df - df.mean()) / df.std()
    
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    kmeans.fit(normalized_df)
    labels = kmeans.labels_
    
    # Map cluster centers to Low/Moderate/High/Very High based on volatility centers
    centers = kmeans.cluster_centers_[:, 0]  # Volatility center index
    sorted_centers_indices = np.argsort(centers)  # indices sorting from lowest vol to highest
    
    mapping = {
        sorted_centers_indices[0]: "Low",
        sorted_centers_indices[1]: "Moderate",
        sorted_centers_indices[2]: "High",
        sorted_centers_indices[3]: "Very High"
    }
    
    return [mapping[label] for label in labels]

# --- 4. Content-Based Fund Recommender ---
def recommend_funds(
    target_risk: str,
    funds_list: List[Dict[str, Any]],
    top_n: int = 3
) -> List[Dict[str, Any]]:
    """
    Recommend top N mutual funds based on desired risk grade, sorting by Sharpe Ratio.
    """
    # Filter by risk category
    filtered = [f for f in funds_list if f.get("risk_category") == target_risk]
    
    # Fallback to risk grade if risk category is missing
    if not filtered:
        filtered = [f for f in funds_list if f.get("risk_grade") == target_risk]
        
    # Sort by Sharpe Ratio (descending)
    sorted_funds = sorted(filtered, key=lambda x: x.get("sharpe_ratio", 0.0) or 0.0, reverse=True)
    
    return sorted_funds[:top_n]
