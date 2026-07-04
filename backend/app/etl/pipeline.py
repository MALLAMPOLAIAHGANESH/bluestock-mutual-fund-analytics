# backend/app/etl/pipeline.py
import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy.orm import Session
from loguru import logger
from datetime import datetime
from app.core.config import settings
from app.database.models import FundHouse, Category, Scheme, NAVHistory, RiskMetrics, Returns, Investor, Transaction, PortfolioHolding, Portfolio

class ETLPipeline:
    def __init__(self, db: Session, raw_dir: Path):
        self.db = db
        self.raw_dir = raw_dir

    def run_pipeline(self):
        logger.info("Starting Mutual Fund ETL Pipeline...")
        
        try:
            # 1. Load static catalogs (Fund Houses, Categories)
            self.load_catalogs()
            
            # 2. Load Schemes Master list
            self.load_schemes()
            
            # 3. Load daily NAV history with ffill and outlier detection
            self.load_nav_history()
            
            # 4. Load Scheme Performance (Returns and Risk Metrics)
            self.load_performance()
            
            # 5. Load Investors and Transactions
            self.load_transactions()
            
            logger.info("ETL Pipeline completed successfully! Database populated.")
            
        except Exception as e:
            logger.error(f"ETL Pipeline failed: {e}")
            self.db.rollback()
            raise e

    def load_catalogs(self):
        logger.info("Loading Fund Houses and Categories catalogs...")
        fm_path = self.raw_dir / "01_fund_master.csv"
        df = pd.read_csv(fm_path)
        
        # Load unique fund houses
        houses = df["fund_house"].dropna().unique()
        for house in houses:
            if not self.db.query(FundHouse).filter(FundHouse.name == house).first():
                fh = FundHouse(name=house)
                self.db.add(fh)
        
        # Load unique categories
        categories = df["category"].dropna().unique()
        for cat in categories:
            if not self.db.query(Category).filter(Category.name == cat).first():
                c = Category(name=cat)
                self.db.add(c)
                
        self.db.commit()
        logger.success("Catalogs loaded successfully.")

    def load_schemes(self):
        logger.info("Loading Schemes Master list...")
        fm_path = self.raw_dir / "01_fund_master.csv"
        df = pd.read_csv(fm_path)
        
        # Eliminate duplicates on AMFI Code
        df = df.drop_duplicates(subset=["amfi_code"])
        
        for _, row in df.iterrows():
            amfi_code = int(row["amfi_code"])
            if self.db.query(Scheme).filter(Scheme.amfi_code == amfi_code).first():
                continue
                
            fh = self.db.query(FundHouse).filter(FundHouse.name == row["fund_house"]).first()
            cat = self.db.query(Category).filter(Category.name == row["category"]).first()
            
            # Parse Date
            launch_date = None
            if pd.notna(row.get("launch_date")):
                try:
                    launch_date = datetime.strptime(row["launch_date"], "%Y-%m-%d").date()
                except ValueError:
                    pass
                    
            scheme = Scheme(
                amfi_code=amfi_code,
                scheme_name=row["scheme_name"],
                fund_house_id=fh.id if fh else None,
                category_id=cat.id if cat else None,
                sub_category=row.get("sub_category"),
                plan=row.get("plan", "Direct"),
                launch_date=launch_date,
                benchmark=row.get("benchmark"),
                expense_ratio_pct=float(row.get("expense_ratio_pct", 0.0) or 0.0),
                exit_load_pct=float(row.get("exit_load_pct", 0.0) or 0.0),
                min_sip_amount=float(row.get("min_sip_amount", 500.0) or 500.0),
                min_lumpsum_amount=float(row.get("min_lumpsum_amount", 1000.0) or 1000.0),
                fund_manager=row.get("fund_manager"),
                risk_category=row.get("risk_category", "Moderate")
            )
            self.db.add(scheme)
            
        self.db.commit()
        logger.success("Schemes master list loaded.")

    def load_nav_history(self):
        logger.info("Loading Daily NAV History...")
        nav_path = self.raw_dir / "02_nav_history.csv"
        df = pd.read_csv(nav_path)
        
        # Missing values detection & forward fill per scheme code
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(by=["amfi_code", "date"])
        
        # Clean duplicate date entries per scheme
        df = df.drop_duplicates(subset=["amfi_code", "date"])
        
        # Outlier detection using rolling Z-Score method
        cleaned_records = []
        for amfi, group in df.groupby("amfi_code"):
            # Ensure scheme exists
            if not self.db.query(Scheme).filter(Scheme.amfi_code == int(amfi)).first():
                continue
                
            group = group.copy()
            # Forward fill missing values
            group["nav"] = group["nav"].ffill()
            
            # Simple outlier detection (Z-score > 4)
            if len(group) > 5:
                rolling_mean = group["nav"].rolling(window=10, min_periods=1).mean()
                rolling_std = group["nav"].rolling(window=10, min_periods=1).std()
                z_scores = (group["nav"] - rolling_mean) / rolling_std.replace(0, 1)
                
                # Replace outliers with rolling mean
                group.loc[z_scores.abs() > 4.0, "nav"] = rolling_mean
                
            for _, row in group.iterrows():
                cleaned_records.append({
                    "amfi_code": int(amfi),
                    "nav_date": row["date"].date(),
                    "nav": float(row["nav"])
                })
                
        # Bulk Insert
        self.db.bulk_insert_mappings(NAVHistory, cleaned_records)
        self.db.commit()
        logger.success(f"NAV History loaded ({len(cleaned_records):,} records).")

    def load_performance(self):
        logger.info("Loading Performance Risk and Returns data...")
        perf_path = self.raw_dir / "07_scheme_performance.csv"
        df = pd.read_csv(perf_path)
        
        for _, row in df.iterrows():
            amfi_code = int(row["amfi_code"])
            if not self.db.query(Scheme).filter(Scheme.amfi_code == amfi_code).first():
                continue
                
            # Populate Returns
            ret = Returns(
                amfi_code=amfi_code,
                return_1yr_pct=float(row.get("return_1yr_pct", 0.0) or 0.0),
                return_3yr_pct=float(row.get("return_3yr_pct", 0.0) or 0.0),
                return_5yr_pct=float(row.get("return_5yr_pct", 0.0) or 0.0),
                benchmark_3yr_pct=float(row.get("benchmark_3yr_pct", 0.0) or 0.0)
            )
            self.db.add(ret)
            
            # Populate RiskMetrics
            risk = RiskMetrics(
                amfi_code=amfi_code,
                sharpe_ratio=float(row.get("sharpe_ratio", 0.0) or 0.0),
                sortino_ratio=float(row.get("sortino_ratio", 0.0) or 0.0),
                treynor_ratio=float(row.get("treynor_ratio", 0.0) or 0.0),
                alpha=float(row.get("alpha", 0.0) or 0.0),
                beta=float(row.get("beta", 1.0) or 1.0),
                std_dev_ann_pct=float(row.get("std_dev_ann_pct", 0.0) or 0.0),
                max_drawdown_pct=float(row.get("max_drawdown_pct", 0.0) or 0.0),
                var_95=float(row.get("var_95", 0.0) or 0.0),
                cvar_95=float(row.get("cvar_95", 0.0) or 0.0),
                tracking_error=float(row.get("tracking_error", 0.0) or 0.0),
                information_ratio=float(row.get("information_ratio", 0.0) or 0.0),
                calmar_ratio=float(row.get("calmar_ratio", 0.0) or 0.0)
            )
            self.db.add(risk)
            
        self.db.commit()
        logger.success("Performance and Risk metrics loaded.")

    def load_transactions(self):
        logger.info("Loading Transactions & Investors behavior...")
        tx_path = self.raw_dir / "08_investor_transactions.csv"
        df = pd.read_csv(tx_path)
        
        # Load unique investors
        investors = df[["investor_id", "age_group", "gender", "annual_income_lakh"]].drop_duplicates(subset=["investor_id"])
        
        for _, row in investors.iterrows():
            if not self.db.query(Investor).filter(Investor.investor_id == row["investor_id"]).first():
                inv = Investor(
                    investor_id=row["investor_id"],
                    age_group=row.get("age_group"),
                    gender=row.get("gender"),
                    annual_income_lakh=float(row.get("annual_income_lakh", 0.0) or 0.0)
                )
                self.db.add(inv)
        self.db.commit()
        
        # Load transactions
        tx_records = []
        df["transaction_date"] = pd.to_datetime(df["transaction_date"])
        
        for _, row in df.iterrows():
            # Verify scheme code exists
            amfi_code = int(row["amfi_code"])
            if not self.db.query(Scheme).filter(Scheme.amfi_code == amfi_code).first():
                continue
                
            tx_records.append({
                "investor_id": row["investor_id"],
                "amfi_code": amfi_code,
                "transaction_type": row["transaction_type"],
                "amount_inr": float(row["amount_inr"]),
                "transaction_date": row["transaction_date"].date(),
                "city_tier": row.get("city_tier"),
                "state": row.get("state")
            })
            
        self.db.bulk_insert_mappings(Transaction, tx_records)
        self.db.commit()
        logger.success(f"Transactions data loaded ({len(tx_records):,} records).")
