import pandas as pd
import numpy as np
import io

class DataEngine:
    def __init__(self):
        self.df = None
        self.meta = {}

    def load_data(self, file_storage):
        """Loads data from a file storage object (CSV)."""
        try:
            # Try utf-8 first, then latin1
            try:
                self.df = pd.read_csv(file_storage, encoding='utf-8')
            except UnicodeDecodeError:
                file_storage.seek(0)
                self.df = pd.read_csv(file_storage, encoding='latin1')
            
            self._clean_column_names()
            return True, "Data loaded successfully"
        except Exception as e:
            return False, str(e)

    def _clean_column_names(self):
        """Standardizes column names to be lower case and snake_case."""
        if self.df is not None:
            self.df.columns = (
                self.df.columns
                .str.strip()
                .str.lower()
                .str.replace(' ', '_')
                .str.replace(r'[^\w]', '', regex=True)
            )

    def analyze_structure(self):
        """Returns metadata about the dataset structure."""
        if self.df is None:
            return None

        # Identify column types
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        date_cols = []
        
        # Heuristic for date columns
        for col in categorical_cols:
            if 'date' in col or 'time' in col:
                try:
                    pd.to_datetime(self.df[col], errors='raise')
                    date_cols.append(col)
                except:
                    pass
        
        # Remove date cols from categorical if identified
        categorical_cols = [c for c in categorical_cols if c not in date_cols]

        self.meta = {
            "rows": int(self.df.shape[0]),
            "columns": int(self.df.shape[1]),
            "column_names": self.df.columns.tolist(),
            "types": {
                "numeric": numeric_cols,
                "categorical": categorical_cols,
                "date": date_cols
            },
            "missing_values": self.df.isnull().sum().to_dict(),
            "duplicate_rows": int(self.df.duplicated().sum())
        }
        return self.meta

    def auto_clean(self):
        """Automatically handles missing values and data types."""
        if self.df is None:
            return

        # 1. Drop duplicates
        self.df.drop_duplicates(inplace=True)

        # 2. Handle Missing Values
        # Numeric -> Fill with Mean
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            self.df[col] = self.df[col].fillna(self.df[col].mean())

        # Categorical -> Try numeric coercion for "Sales" like data, then fill with Mode
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols:
            # Heuristic: If it contains currency or numbers but is 'object', try to convert
            if any(key in col.lower() for key in ['sales', 'price', 'profit', 'cost', 'revenue', 'amount']):
                try:
                    # Remove currency symbols and commas
                    temp_col = self.df[col].astype(str).str.replace(r'[$,]', '', regex=True)
                    numeric_series = pd.to_numeric(temp_col, errors='coerce')
                    if numeric_series.notnull().mean() > 0.5: # If half are numeric
                        self.df[col] = numeric_series.fillna(numeric_series.mean())
                        continue # Skip to next column as this is now numeric
                except:
                    pass

            if not self.df[col].mode().empty:
                self.df[col] = self.df[col].fillna(self.df[col].mode()[0])
            else:
                self.df[col] = self.df[col].fillna("Unknown")

        # 3. Date Coercion
        for col in self.meta.get("types", {}).get("date", []):
            self.df[col] = pd.to_datetime(self.df[col], errors='coerce')

        return True

    def get_summary_stats(self):
        """Returns descriptive statistics for numeric columns."""
        if self.df is None:
            return {}
        return self.df.describe().to_dict()

    def get_preview(self, rows=5):
        """Returns the first N rows as a dictionary."""
        if self.df is None:
            return []
        # Convert date columns to string for JSON serialization
        temp_df = self.df.copy()
        for col in temp_df.columns:
             if pd.api.types.is_datetime64_any_dtype(temp_df[col]):
                 temp_df[col] = temp_df[col].dt.strftime('%Y-%m-%d')
        return temp_df.head(rows).to_dict(orient='records')
