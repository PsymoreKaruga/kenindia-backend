# backend/calculator/utils/rates_loader.py
import pandas as pd
from pathlib import Path
import warnings

class RateTable:
    def __init__(self):
        self.tables = {}
        self._load_all_tables()

    def _load_all_tables(self):
        product_paths = {
            "education_endowment": "EDUCATION ENDOWMENT POLICY PLAN.xlsx",
            "academic_advantage": "ACADEMIC ADVANTAGE PLAN.xlsx",
            "money_back_15": "15 YEARS MONEY BACK PLAN.xlsx",
            "money_back_10": "10 YEARS MONEY BACK PLAN.xlsx",
        }

        for product, file_name in product_paths.items():
            path = Path(__file__).resolve().parent.parent / "data" / file_name
            if not path.exists():
                warnings.warn(f"File not found for {product}: {path}")
                continue

            xls = pd.ExcelFile(path, engine="openpyxl")
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(path, sheet_name=sheet_name, header=None, engine="openpyxl")
                try:
                    if product in ["education_endowment", "academic_advantage"]:
                        # 2D table parsing: attempt to coerce headers/ages to numeric and drop non-numeric rows
                        raw_terms = df.iloc[1, 1:12]
                        terms_numeric = pd.to_numeric(raw_terms, errors="coerce").dropna()
                        if terms_numeric.empty:
                            warnings.warn(f"No numeric term headers found in sheet '{sheet_name}' of {file_name}")
                            continue
                        terms = terms_numeric.astype(int).values

                        raw_ages = df.iloc[2:, 0]
                        ages_numeric = pd.to_numeric(raw_ages, errors="coerce").dropna()
                        if ages_numeric.empty:
                            warnings.warn(f"No numeric ages found in sheet '{sheet_name}' of {file_name}")
                            continue
                        ages = ages_numeric.astype(int).values

                        # slice rates matrix using lengths found (safe bounds)
                        rates_block = df.iloc[2: 2 + len(ages), 1: 1 + len(terms)]
                        # coerce to numeric and replace non-numeric with NaN
                        rates_data = rates_block.apply(pd.to_numeric, errors="coerce").values

                        rate_df = pd.DataFrame(rates_data, index=ages, columns=terms)
                        rate_df = rate_df.replace(0.0, float("nan"))
                    else:
                        # 1D table parsing for fixed-term products - first column ages, second column rates
                        # Coerce both columns together and drop rows where either is non-numeric to keep alignment
                        two_col = df.iloc[:, 0:2].copy()
                        two_col.columns = ["age", "rate"]
                        two_col["age"] = pd.to_numeric(two_col["age"], errors="coerce")
                        two_col["rate"] = pd.to_numeric(two_col["rate"], errors="coerce")
                        two_col = two_col.dropna(subset=["age", "rate"])  # keep only rows with both values
                        if two_col.empty:
                            warnings.warn(f"No numeric age-rate pairs found in sheet '{sheet_name}' of {file_name}")
                            continue
                        ages = two_col["age"].astype(int).values
                        rates = two_col["rate"].astype(float).values
                        rate_df = pd.Series(rates, index=ages)

                    # store lowercase product key -> rate table (DataFrame or Series)
                    self.tables[product.lower()] = rate_df
                except Exception as e:
                    warnings.warn(f"Failed to parse sheet '{sheet_name}' in {file_name}: {e}")

    def get_rate(self, product_key, discounted_age, term):
        df = self.tables.get(product_key.lower())
        if df is None:
            return None

        try:
            if isinstance(df, pd.DataFrame):  # 2D table
                rate = df.at[discounted_age, term]
            else:  # 1D Series, ignore term
                rate = df.at[discounted_age]
            if pd.isna(rate):
                return None
            return float(rate)
        except KeyError:
            return None
        
