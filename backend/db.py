import os
import queue
import time
import pymysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "pricing_system")

class ConnectionPool:
    def __init__(self, size=5, max_wait=5.0):
        self.size = size
        self.max_wait = max_wait
        self.pool = queue.Queue(maxsize=size)
        for _ in range(size):
            conn = self._create_connection()
            if conn:
                self.pool.put(conn)

    def _create_connection(self):
        try:
            return pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                autocommit=True,
                cursorclass=pymysql.cursors.DictCursor
            )
        except Exception as e:
            print(f"[DB] Error creating connection: {e}")
            return None

    def get_connection(self):
        try:
            # Try to get connection from pool
            conn = self.pool.get(timeout=self.max_wait)
            # Ping database to verify connection is alive
            conn.ping(reconnect=True)
            return conn
        except queue.Empty:
            # If empty, try to create an ad-hoc connection
            print("[DB] Connection pool exhausted. Creating temporary connection...")
            return self._create_connection()
        except Exception as e:
            print(f"[DB] Error getting connection: {e}")
            return self._create_connection()

    def release_connection(self, conn):
        if conn is None:
            return
        try:
            self.pool.put(conn, block=False)
        except queue.Full:
            # If pool is full (due to ad-hoc connection), close it
            try:
                conn.close()
            except:
                pass

# Initialize global pool instance
# The DB_NAME database might not exist yet, so we catch errors during connection initialization
db_pool = None
try:
    db_pool = ConnectionPool(size=10)
except Exception as e:
    print(f"[DB] Pool creation deferred: {e}")

class db_session:
    """
    Context manager to easily get a connection and cursor.
    Usage:
        with db_session() as cursor:
            cursor.execute("SELECT * FROM products")
            result = cursor.fetchall()
    """
    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        global db_pool
        if db_pool is None:
            db_pool = ConnectionPool(size=10)
        self.conn = db_pool.get_connection()
        if not self.conn:
            raise Exception("Unable to establish connection to database.")
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            global db_pool
            if db_pool:
                db_pool.release_connection(self.conn)
            else:
                try:
                    self.conn.close()
                except:
                    pass
