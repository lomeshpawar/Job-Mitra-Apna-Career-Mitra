"""
Job Mitra - Database Layer
Provides unified access to SQLite and MySQL with foreign keys enabled and transactional integrity.
"""
import sqlite3
from config import Config

def get_db_connection():
    """Returns an active database connection and engine name ('sqlite' or 'mysql')."""
    if Config.DB_ENGINE in ('mysql', 'auto'):
        try:
            import pymysql
            conn = pymysql.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
                connect_timeout=2
            )
            return conn, 'mysql'
        except ImportError:
            if Config.DB_ENGINE == 'mysql':
                raise RuntimeError("PyMySQL package is required when DB_ENGINE is set to 'mysql'. Please run: pip install pymysql")
        except Exception as e:
            if Config.DB_ENGINE == 'mysql':
                raise RuntimeError(f"Configured MySQL engine failed to connect: {e}")

    # SQLite fallback
    conn = sqlite3.connect(Config.DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn, 'sqlite'

def query_db(query, params=(), one=False, commit=False):
    """
    Executes a SQL query with proper parameter binding.
    Supports both %s and ? parameter placeholders dynamically.
    """
    conn, engine = get_db_connection()
    try:
        cur = conn.cursor()
        if engine == 'sqlite':
            # Convert MySQL %s to SQLite ?
            query = query.replace('%s', '?')
        cur.execute(query, params)
        if commit:
            if engine == 'sqlite':
                conn.commit()
            else:
                conn.commit()
            return cur.lastrowid
        res = cur.fetchall()
        if engine == 'sqlite':
            res = [dict(row) for row in res]
        return (res[0] if res else None) if one else res
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def execute_transaction(operations):
    """
    Executes a sequence of queries inside an atomic transaction.
    operations: list of tuples (query, params)
    """
    conn, engine = get_db_connection()
    try:
        cur = conn.cursor()
        last_id = None
        for query, params in operations:
            if engine == 'sqlite':
                query = query.replace('%s', '?')
            cur.execute(query, params)
            last_id = cur.lastrowid
        conn.commit()
        return last_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
