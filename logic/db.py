import psycopg2
from psycopg2 import OperationalError, InterfaceError, DatabaseError
from dotenv import load_dotenv
import os, logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("db_port")
DBNAME = os.getenv("dbname")

_missing = [k for k, v in {"user": USER, "password": PASSWORD, "host": HOST, "port": PORT, "dbname": DBNAME}.items() if not v]
if _missing:
    logging.critical(f"Missing required database environment variables: {_missing}")


class DatabaseConnection:
    def __init__(self):
        '''Initialize the database connection'''
        self.connection = None
        self.cursor = None
        try:
            self.connection = psycopg2.connect(
                user=USER,
                password=PASSWORD,
                host=HOST,
                port=PORT,
                dbname=DBNAME,
                sslmode="require"       
            )
            self.connection.autocommit = False
            self.cursor = self.connection.cursor()
            logging.info("Database connection successful.")
        except OperationalError as e:
            logging.error(f"Failed to connect to database: {e}")
        except Exception as e:
            logging.error(f"Unexpected error during database connection: {e}")

    def _is_connected(self) -> bool:
        '''Check if the connection and cursor are active and healthy'''
        if not self.connection or self.connection.closed != 0:
            return False
        if not self.cursor or self.cursor.closed:
            return False
        return True

    def execute_query(self, query, values):
        '''
        Execute a SQL query
        Args:
            query (str): The SQL query to execute
            values (tuple): The values to pass to the query
        Returns:
            Boolean: True if the query was executed successfully, False otherwise
        '''
        if not self._is_connected():
            logging.warning("No active database connection. Cannot execute query.")
            return False
        try:
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
        except (OperationalError, InterfaceError) as e:
            
            logging.error(f"Connection error during query execution: {e}")
            self._safe_rollback()
            raise  
        except DatabaseError as e:
            logging.error(f"Query execution failed: {e}")
            self._safe_rollback()
            return False
        except Exception as e:
            logging.error(f"Unexpected error during query execution: {e}")
            self._safe_rollback()
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
        if not self._is_connected():
            logging.warning("No active database connection. Cannot fetch data.")
            return None
        try:
            self.cursor.execute(query, values)
            return self.cursor.fetchall()
        except (OperationalError, InterfaceError) as e:
            logging.error(f"Connection error during fetch: {e}")
            self._safe_rollback()
            raise
        except DatabaseError as e:
            logging.error(f"Failed to fetch data: {e}")
            self._safe_rollback()
            return None
        except Exception as e:
            logging.error(f"Unexpected error during fetch: {e}")
            self._safe_rollback()
            return None

    def get_connection(self):
        '''Returns the active connection object, or None if not connected'''
        if self._is_connected():
            return self.connection
        logging.warning("No active connection to return.")
        return None

    def _safe_rollback(self):
        '''Rollback without raising if connection is already broken'''
        try:
            if self.connection and self.connection.closed == 0:
                self.connection.rollback()
        except Exception as e:
            logging.warning(f"Rollback failed: {e}")

    def close(self):
        '''Close the cursor and database connection'''
        try:
            if self.cursor and not self.cursor.closed:
                self.cursor.close()
        except Exception as e:
            logging.warning(f"Error closing cursor: {e}")
        try:
            if self.connection and self.connection.closed == 0:
                self.connection.close()
                logging.info("Database connection closed.")
        except Exception as e:
            logging.warning(f"Error closing connection: {e}")

    def __enter__(self):
        '''Allow use as a context manager: with DatabaseConnection() as db'''
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        '''Auto-close on exit from context manager'''
        self.close()
