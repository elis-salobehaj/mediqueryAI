import sqlite3
import json
import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Resolve relative to this file: ../data
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.data_dir = os.path.join(base_dir, "data")
        else:
            self.data_dir = data_dir
            
        # Use file-based DB to allow sharing with LlamaIndex/SQLAlchemy
        db_path = os.path.join(base_dir, "medical.db")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._load_data()

    def _load_data(self):
        """Loads CSV files from data_dir into SQLite tables."""
        if not os.path.exists(self.data_dir):
            logger.warning(f"Data directory {self.data_dir} not found.")
            return

        csv_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
        
        for csv_file in csv_files:
            table_name = os.path.splitext(csv_file)[0]
            file_path = os.path.join(self.data_dir, csv_file)
            try:
                df = pd.read_csv(file_path)
                df.to_sql(table_name, self.conn, index=False, if_exists='replace')
                logger.info(f"Loaded {table_name} with {len(df)} rows.")
            except Exception as e:
                logger.error(f"Failed to load {csv_file}: {e}")

    def get_schema(self) -> str:
        """Returns a string representation of the database schema for the LLM, enriched with semantic metadata."""
        schema_str = []
        
        # Load semantic metadata if available
        meta_path = os.path.join(self.data_dir, "semantic_metadata.json")
        metadata = {}
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r') as f:
                    meta_list = json.load(f)
                    for item in meta_list:
                        metadata[item['table_name']] = item
            except Exception as e:
                logger.error(f"Failed to load semantic metadata: {e}")

        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in self.cursor.fetchall()]
        
        for table in tables:
            table_desc = ""
            col_meta = {}
            if table in metadata:
                table_desc = f" - {metadata[table].get('description', '')}"
                col_meta = metadata[table].get('columns', {})

            self.cursor.execute(f"PRAGMA table_info({table})")
            columns = []
            for row in self.cursor.fetchall():
                col_name = row[1]
                col_type = row[2]
                desc = f" - {col_meta.get(col_name, '')}" if col_name in col_meta else ""
                columns.append(f"{col_name} ({col_type}){desc}")
            
            schema_str.append(f"Table: {table}{table_desc}\nColumns: {', '.join(columns)}")
        
        return "\n\n".join(schema_str)
    
    def get_all_table_names(self) -> list[str]:
        """Returns a list of all table names in the database."""
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_table_schema(self, table_name: str) -> list[tuple[str, str]]:
        """
        Returns the schema for a specific table as a list of (column_name, column_type) tuples.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of tuples containing (column_name, column_type)
        """
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
            # We want just name (index 1) and type (index 2)
            return [(row[1], row[2]) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get schema for table {table_name}: {e}")
            return []

    def execute_query(self, sql_query: str):
        """Executes a SQL query and returns the results as a list of dictionaries."""
        try:
            # Strip trailing semicolons for consistency
            sql_clean = sql_query.strip().rstrip(';')
            df = pd.read_sql_query(sql_clean, self.conn)
            return {
                "columns": df.columns.tolist(),
                "data": df.to_dict(orient="records"),
                "row_count": len(df)
            }
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise e

    def validate_sql(self, sql_query: str) -> dict:
        """
        Validates a SQL query through dry-run execution and sanity checks.
        
        Returns:
            dict with keys:
                - valid (bool): True if query is valid
                - error (str | None): Error message if invalid
                - row_count (int | None): Estimated row count (None if error)
                - warnings (list): List of warning messages
        """
        warnings = []
        
        # Strip trailing semicolons - SQLite doesn't handle them well in EXPLAIN or subqueries
        sql_clean = sql_query.strip().rstrip(';')
        
        try:
            # Use EXPLAIN QUERY PLAN for dry-run validation (SQLite specific)
            explain_query = f"EXPLAIN QUERY PLAN {sql_clean}"
            self.cursor.execute(explain_query)
            self.cursor.fetchall()  # Consume results
            
            # If EXPLAIN succeeded, try to get row count estimate
            # For safety, we'll use LIMIT to avoid actually fetching large results
            count_query = f"SELECT COUNT(*) as count FROM ({sql_clean})"
            self.cursor.execute(count_query)
            row_count = self.cursor.fetchone()[0]
            
            # Sanity checks
            if row_count == 0:
                warnings.append("Query returns 0 rows - may indicate incorrect filters or empty tables")
            elif row_count > 10000:
                warnings.append(f"Query returns {row_count} rows - unusually high, may need additional filters")
            
            return {
                "valid": True,
                "error": None,
                "row_count": row_count,
                "warnings": warnings
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"SQL validation failed: {error_msg}")
            return {
                "valid": False,
                "error": error_msg,
                "row_count": None,
                "warnings": []
            }

# Singleton instance
db_service = DatabaseService()
