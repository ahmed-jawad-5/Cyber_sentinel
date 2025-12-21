import os
import pandas as pd

from db.storage import Database


class DataController:

    def __init__(self):
        self.df = None
        self.original_df = None

    # ---------------- CSV LOAD/SAVE -----------------
    def load_csv(self, path):
        try:
            self.df = pd.read_csv(path)
            self.original_df = self.df.copy()
            return True, "File loaded."
        except Exception as e:
            return False, str(e)

    def save_csv(self, path):
        try:
            self.df.to_csv(path, index=False)
            return True, "File saved."
        except Exception as e:
            return False, str(e)

    def restore_original(self):
        if self.original_df is not None:
            self.df = self.original_df.copy()
            return True
        return False

    # ---------------- DATABASE INTEGRATION -----------------
    def save_to_db(self, db_root: str, table_name: str, primary_key: str = "id"):
        """Persist the current DataFrame into the custom Database.

        Creates/overwrites a table named `table_name` under `db_root`.
        """
        if self.df is None:
            return False, "No data loaded to save."

        os.makedirs(db_root, exist_ok=True)
        temp_csv = os.path.join(db_root, f"{table_name}.csv")

        try:
            # Export current dataframe snapshot
            self.df.to_csv(temp_csv, index=False)

            db = Database(root=db_root)
            db.load()

            # Replace table if it already exists
            if table_name in db.tables:
                db.tables.pop(table_name, None)

            db.import_csv(
                table_name=table_name,
                csv_path=temp_csv,
                primary_key=primary_key,
                sorted_indexes=None,
            )
            db.save()
            return True, f"Saved {len(self.df)} rows to table '{table_name}' in database at '{db_root}'."
        except Exception as e:
            return False, f"Failed to save to database: {e}"

    def load_from_db(self, db_root: str, table_name: str):
        """Load all rows from a Database table into the DataFrame."""
        try:
            db = Database(root=db_root)
            db.load()
            tbl = db.table(table_name)
            rows = tbl.select()

            self.df = pd.DataFrame(rows)
            self.original_df = self.df.copy()
            return True, f"Loaded {len(self.df)} rows from table '{table_name}'."
        except Exception as e:
            return False, f"Failed to load from database: {e}"
