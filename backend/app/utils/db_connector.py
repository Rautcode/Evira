import os
import pyodbc
from dotenv import load_dotenv
from typing import Optional
from app.utils.config_manager import config_manager

# Load environment variables from .env
load_dotenv()

class DBConnector:
    def __init__(self, 
                 server: Optional[str] = None, 
                 database: Optional[str] = None, 
                 username: Optional[str] = None, 
                 password: Optional[str] = None, 
                 auth_type: Optional[str] = None):
                 
        config = config_manager.load_config()
                 
        self.server = server or config.get("mssql_server", os.getenv("MSSQL_SERVER"))
        self.database = database or config.get("mssql_database", os.getenv("MSSQL_DATABASE"))
        self.username = username or config.get("mssql_username", os.getenv("MSSQL_USERNAME"))
        self.password = password or config.get("mssql_password", os.getenv("MSSQL_PASSWORD"))
        self.auth_type = (auth_type or config.get("mssql_auth_type", os.getenv("MSSQL_AUTH_TYPE", "sql"))).lower()

    def get_connection(self):
        if not self.server:
            raise ValueError("Server must be specified (either as argument or in .env)")
            
        drivers = [
            'ODBC Driver 17 for SQL Server',
            'SQL Server'
        ]
        
        # Find available driver
        available_driver = None
        for driver in drivers:
            try:
                if driver in [d for d in pyodbc.drivers()]:
                    available_driver = driver
                    break
            except:
                continue
                
        if not available_driver:
            raise RuntimeError("No suitable SQL Server driver found")
            
        try:
            if self.auth_type == "windows":
                # Try to connect without specifying database first
                conn_str = f"DRIVER={available_driver};SERVER={self.server};Trusted_Connection=yes;"
                
                conn = pyodbc.connect(conn_str)
                conn.autocommit = True
                
                # Create database if it doesn't exist
                cursor = conn.cursor()
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = N'scada_reports')
                    BEGIN
                        CREATE DATABASE scada_reports;
                    END
                """)
                conn.autocommit = False
                
                # Switch to the database
                conn.close()
                conn = pyodbc.connect(conn_str + "DATABASE=scada_reports;")
                return conn
                
            else:  # SQL Server authentication
                if not self.username or not self.password:
                    raise ValueError("Username and password required for SQL authentication")
                    
                conn_str = (
                    f"DRIVER={available_driver};"
                    f"SERVER={self.server};"
                    f"UID={self.username};"
                    f"PWD={self.password};"
                )
                
                if self.database:
                    conn_str += f"DATABASE={self.database};"
                    
                return pyodbc.connect(conn_str)
                
        except Exception as e:
            raise RuntimeError(f"Database connection failed: {str(e)}")
