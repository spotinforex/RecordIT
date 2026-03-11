import psycopg2
from dotenv import load_dotenv
import os, logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")


class DatabaseConnection:
    def __init__(self):
        '''Initialize the database connection'''
        try:
            self.connection = None
            self.cursor = None
            self.connection = psycopg2.connect(
                user=USER,
                password=PASSWORD,
                host=HOST,
                port=PORT,
                dbname=DBNAME,
                sslmode="require"
            )
            logging.info("Connection successful!")
            self.cursor = self.connection.cursor()
        except Exception as e:
            logging.error(f"Failed to connect: {e}")

    def execute_query(self, query, values):
        '''
        Execute a SQL query
        Args:
            query (str): The SQL query to execute
            values (tuple): The values to pass to the query
        Returns:
            Boolean: True if the query was executed successfully, False otherwise
        '''
        if not self.connection or not self.cursor:
            logging.warning("No database connection.")
            return False

        try:
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            logging.error(f"Query execution failed: {e}")
            return False  

    def fetch_all(self, query, values=None):
        '''
        Fetch all results from a SQL query
        Args:
            query (str): The SQL query to execute
            values (tuple, optional): Parameterized values to pass to the query
        Returns:
            list: A list of tuples containing the query results, or None if an error occurs
        '''
        if not self.connection or not self.cursor:
            logging.warning("No database connection.")
            return None

        try:
            self.cursor.execute(query, values)
            return self.cursor.fetchall()
        except Exception as e:
            self.connection.rollback()
            logging.error(f"Failed to fetch data: {e}")
            return None

    def close(self):
        '''Close the cursor and database connection'''
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            logging.info("Connection closed.")
