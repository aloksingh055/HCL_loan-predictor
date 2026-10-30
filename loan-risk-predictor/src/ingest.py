import os
import pandas as pd
import psycopg2
import logging

# Logging configuration setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataIngestion:
    def __init__(self, db_config=None):
        self.db_config = db_config or {
            "dbname": "postgres",
            "user": "postgres",
            "password": "alok@1234",
            "host": "localhost",
            "port": "5432"
        }

    def load_data_from_db(self, query: str) -> pd.DataFrame:
        """
        PostgreSQL database se data query karke Pandas DataFrame return karta hai.
        """
        try:
            logging.info("Connecting to PostgreSQL database...")
            connection = psycopg2.connect(**self.db_config)
            logging.info("Connection established successfully. Fetching data...")
            df = pd.read_sql(query, connection)
            connection.close()
            logging.info(f"Data fetched successfully with shape: {df.shape}")
            return df
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            logging.info("Fallback: Generating sample/mock dataset for testing pipeline...")
            return self._generate_mock_data()

    def _generate_mock_data(self) -> pd.DataFrame:
        """
        Agar database available na ho, toh testing ke liye realistic mock bank loan dataset generate karta hai.
        """
        import numpy as np
        np.random.seed(42)
        n_samples = 5000
        
        data = {
            'age': np.random.randint(21, 70, size=n_samples),
            'income': np.random.randint(20000, 150000, size=n_samples),
            'loan_amount': np.random.randint(5000, 50000, size=n_samples),
            'credit_score': np.random.randint(300, 850, size=n_samples),
            'employment_length': np.random.randint(0, 20, size=n_samples),
            'debt_to_income_ratio': np.random.uniform(0.1, 0.9, size=n_samples),
        }
        df = pd.DataFrame(data)
        # Target variable: Default (1) or Non-Default (0)
        df['default'] = np.where((df['credit_score'] < 580) | (df['debt_to_income_ratio'] > 0.6), 1, 0)
        
        # Save mock data to data folder
        os.makedirs("data", exist_ok=True)
        df.to_csv("data/loan_data.csv", index=False)
        logging.info("Mock dataset generated and saved to data/loan_data.csv")
        return df

if __name__ == "__main__":
    ingestor = DataIngestion()
    query = "SELECT * FROM loan_transactions;"
    df = ingestor.load_data_from_db(query)
    print(df.head())