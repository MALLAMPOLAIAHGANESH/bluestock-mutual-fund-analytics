"""
recommender.py
==============
Simple Mutual Fund Recommender based on investor risk appetite.

Usage:
    py recommender.py                   # Demo: all three profiles
    py recommender.py --risk Low        # Command-line mode
    py recommender.py --risk Moderate
    py recommender.py --risk High
"""

import argparse
import os
import sys

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data", "processed")
PERF_CSV = os.path.join(DATA_DIR, "07_scheme_performance.csv")

# ---------------------------------------------------------------------------
# Risk grade mapping
# ---------------------------------------------------------------------------
RISK_MAP = {
    "Low":      ["Low"],
    "Moderate": ["Moderate", "Moderately High"],
    "High":     ["High", "Very High"],
}

RISK_DESCRIPTIONS = {
    "Low":      "Capital preservation with stable, predictable returns (Debt / Gilt funds).",
    "Moderate": "Balanced risk-return; predominantly large-cap equity funds.",
    "High":     "Aggressive growth; mid-cap, small-cap, ELSS funds.",
}


# ---------------------------------------------------------------------------
# Core recommender function
# ---------------------------------------------------------------------------
def recommend(risk_appetite: str, top_n: int = 3) -> pd.DataFrame:
    """
    Return top_n fund recommendations for a given risk appetite.

    Parameters
    ----------
    risk_appetite : str
        One of 'Low', 'Moderate', 'High'
    top_n : int
        Number of funds to recommend (default 3)

    Returns
    -------
    pd.DataFrame  -- columns: scheme_name, fund_house, category,
                              sharpe_ratio, return_3yr_pct, std_dev_ann_pct,
                              expense_ratio_pct, risk_grade
    """
    risk_appetite = risk_appetite.strip().title()
    if risk_appetite not in RISK_MAP:
        raise ValueError(
            f"Invalid risk appetite '{risk_appetite}'. "
            f"Choose from: {list(RISK_MAP.keys())}"
        )

    df = pd.read_csv(PERF_CSV)

    # Filter by matching risk grades
    matching_grades = RISK_MAP[risk_appetite]
    filtered = df[df["risk_grade"].isin(matching_grades)].copy()

    if filtered.empty:
        raise RuntimeError(
            f"No funds found for risk appetite '{risk_appetite}'. "
            f"Matched grades: {matching_grades}"
        )

    # Rank by Sharpe ratio (descending); break ties by 3-yr return
    filtered = filtered.sort_values(
        ["sharpe_ratio", "return_3yr_pct"], ascending=[False, False]
    )
    top = filtered.head(top_n)

    cols = [
        "scheme_name", "fund_house", "category",
        "sharpe_ratio", "return_3yr_pct", "std_dev_ann_pct",
        "expense_ratio_pct", "risk_grade",
    ]
    return top[cols].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Pretty printer
# ---------------------------------------------------------------------------
def print_recommendation(risk_appetite: str, top_n: int = 3) -> None:
    """Print a formatted recommendation table to stdout."""
    risk_appetite = risk_appetite.strip().title()
    result = recommend(risk_appetite, top_n)

    width = 95
    print("\n" + "=" * width)
    print(f"  MUTUAL FUND RECOMMENDER  |  Risk Appetite: {risk_appetite.upper()}")
    print("=" * width)
    print(f"  Profile : {RISK_DESCRIPTIONS[risk_appetite]}")
    print(f"  Method  : Ranked by Sharpe Ratio (higher = better risk-adjusted return)")
    print("-" * width)

    header = (
        f"{'#':<4}"
        f"{'Fund Name':<47}"
        f"{'Category':<18}"
        f"{'Sharpe':>7}"
        f"{'3Y Ret%':>8}"
        f"{'Std Dev%':>9}"
        f"{'Exp Ratio%':>11}"
    )
    print(header)
    print("-" * width)

    for rank, (_, row) in enumerate(result.iterrows(), start=1):
        name = row["scheme_name"]
        if len(name) > 45:
            name = name[:42] + "..."
        line = (
            f"{rank:<4}"
            f"{name:<47}"
            f"{row['category']:<18}"
            f"{row['sharpe_ratio']:>7.2f}"
            f"{row['return_3yr_pct']:>8.2f}"
            f"{row['std_dev_ann_pct']:>9.2f}"
            f"{row['expense_ratio_pct']:>11.2f}"
        )
        print(line)

    print("-" * width)
    print(f"\n  Top {top_n} funds recommended for '{risk_appetite}' risk investors.")
    print(f"  DISCLAIMER: Educational purposes only. Consult a SEBI-registered advisor.")
    print("=" * width + "\n")


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
def _risk_type(value: str) -> str:
    """Normalise risk appetite input to title-case and validate."""
    normalised = value.strip().title()
    if normalised not in RISK_MAP:
        valid = ", ".join(RISK_MAP.keys())
        raise argparse.ArgumentTypeError(
            f"Invalid risk appetite '{value}'. Choose from: {valid} (case-insensitive)"
        )
    return normalised


def main():
    parser = argparse.ArgumentParser(
        description="Simple Mutual Fund Recommender -- input risk appetite, get top 3 funds."
    )
    parser.add_argument(
        "--risk",
        type=_risk_type,          # case-insensitive: low/LOW/Low all accepted
        metavar="{Low,Moderate,High}",
        help="Investor risk appetite: Low | Moderate | High (case-insensitive)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="Number of funds to recommend (default: 3)",
    )
    args = parser.parse_args()

    if args.risk:
        print_recommendation(args.risk, args.top)
    else:
        # Interactive mode
        print("\n" + "=" * 60)
        print("  Mutual Fund Recommender -- Interactive Mode")
        print("=" * 60)
        print("  Risk Appetite Options:")
        print("    1. Low      -- Stable, low-risk funds (Debt / Gilt)")
        print("    2. Moderate -- Balanced funds (Large Cap Equity)")
        print("    3. High     -- Aggressive funds (Mid/Small Cap, ELSS)")
        print("-" * 60)

        while True:
            user_input = input("\n  Enter risk appetite (Low / Moderate / High) or 'q' to quit: ").strip()
            if user_input.lower() in ("q", "quit", "exit"):
                print("\n  Goodbye! Invest wisely.\n")
                sys.exit(0)
            try:
                print_recommendation(user_input, args.top)
                another = input("  Run again? (y/n): ").strip().lower()
                if another != "y":
                    print("\n  Goodbye! Invest wisely.\n")
                    break
            except ValueError as e:
                print(f"\n  Error: {e}")


# ---------------------------------------------------------------------------
# Demo: run all three risk profiles when called directly (no args)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("\n" + "#" * 95)
        print("  BLUESTOCK MF CAPSTONE -- Fund Recommender Demo (All Risk Profiles)")
        print("#" * 95)
        for profile in ["Low", "Moderate", "High"]:
            print_recommendation(profile, top_n=3)
    else:
        main()
