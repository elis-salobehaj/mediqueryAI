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

    def execute_query(self, sql_query: str):
        """Executes a SQL query and returns the results as a list of dictionaries."""
        try:
            df = pd.read_sql_query(sql_query, self.conn)
            return {
                "columns": df.columns.tolist(),
                "data": df.to_dict(orient="records"),
                "row_count": len(df)
            }
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise e

# Singleton instance
db_service = DatabaseService()
