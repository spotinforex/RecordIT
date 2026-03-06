# Test script to verify database connection and query execution
from app.db import DatabaseConnection
if __name__ == "__main__":
    db = DatabaseConnection()
    data = db.fetch_all("SELECT * FROM complaint;")
    print(data)
    db.close()