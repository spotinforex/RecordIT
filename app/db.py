import psycopg2
from dotenv import load_dotenv
import os, logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# Connect to the database
class DatabaseConnection:
    def __init__(self):
        '''Initialize the database connection'''
        try:
            self.connection = psycopg2.connect(
                user=USER,
                password=PASSWORD,
                host=HOST,
                port=PORT,
                dbname=DBNAME
            )
            logging.info("Connection successful!")
            self.cursor = self.connection.cursor()
        except Exception as e:
            logging.error(f"Failed to connect: {e}")

    def execute_query(self, query):
        '''
        Execute a SQL query
        Args:
            query (str): The SQL query to execute
        Returns:
            Boolean: True if the query was executed successfully, False otherwise
        '''
        if self.cursor:
            try:
                self.cursor.execute(query)
                return True
            except Exception as e:
                logging.error(f"Query execution failed: {e}")
                return
        else:
            logging.warning("No database connection.")

    def fetch_all(self, query):
        '''Fetch all results from a SQL query
        Args:
            query (str): The SQL query to execute
        Returns:
            list: A list of tuples containing the query results, or None if an error occurs
        '''
        if self.cursor:
            try:
                self.cursor.execute(query)
                return self.cursor.fetchall()
            except Exception as e:
                logging.error(f"Failed to fetch data: {e}")
        else:
            logging.warning("No database connection.")

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            logging.info("Connection closed.")

