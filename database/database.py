"""
Updated Database Manager for PostgreSQL - Compatible with migration system
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import sys

class DatabaseManager:
    """PostgreSQL Database Manager for localhost connection"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connection_pool = None
        self.load_config()
        self.setup_connection_pool()
    
    def load_config(self):
        """Load database configuration from environment variables"""
        load_dotenv()
        
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'persian_crm_db'),
            'user': os.getenv('DB_USER', 'crm_user'),
            'password': os.getenv('DB_PASSWORD', 'crm_password_2024')
        }
        
        self.pool_config = {
            'minconn': 1,
            'maxconn': int(os.getenv('DB_POOL_SIZE', '5')),
        }
        
        # Check if SSH tunnel is needed (should be false for localhost)
        self.use_ssh_tunnel = os.getenv('USE_SSH_TUNNEL', 'false').lower() == 'true'
        
        if self.use_ssh_tunnel:
            self.logger.warning("SSH tunnel is enabled but not needed for localhost PostgreSQL")
        
        self.logger.info(f"Database config loaded: {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}")
    
    def setup_connection_pool(self):
        """Setup PostgreSQL connection pool"""
        try:
            self.connection_pool = SimpleConnectionPool(
                **self.pool_config,
                **self.db_config,
                cursor_factory=RealDictCursor
            )
            self.logger.info(f"Database connection pool created successfully")
            
        except psycopg2.Error as e:
            self.logger.error(f"Failed to create database connection pool: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error creating connection pool: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connection and verify tables exist"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Test basic connection
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()
                    self.logger.info(f"Connected to: {version['version'][:50]}...")
                    
                    # Check if our tables exist - Updated table names to match schema
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name IN ('deals', 'deal_activities', 'crmteam', 'sentiment_analysis')
                    """)
                    
                    existing_tables = [row['table_name'] for row in cursor.fetchall()]
                    required_tables = ['deals', 'deal_activities', 'crmteam', 'sentiment_analysis']
                    missing_tables = set(required_tables) - set(existing_tables)
                    
                    if missing_tables:
                        self.logger.warning(f"Missing tables: {missing_tables}")
                        self.logger.warning("Please run the database setup script first")
                    else:
                        self.logger.info("All required tables exist")
                    
                    return True
                        
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            if conn:
                yield conn
            else:
                raise Exception("Unable to get database connection from pool")
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def _convert_query_placeholders(self, query: str) -> str:
        """Convert ? placeholders to PostgreSQL %s format (used by psycopg2)"""
        if '?' not in query:
            return query
        
        # Simply replace all ? with %s for psycopg2
        return query.replace('?', '%s')
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Convert ? placeholders to PostgreSQL %s format
                    pg_query = self._convert_query_placeholders(query)
                    
                    # Ensure params is a tuple for psycopg2
                    if params is not None and not isinstance(params, tuple):
                        if isinstance(params, list):
                            params = tuple(params)
                        else:
                            params = (params,)
                    
                    cursor.execute(pg_query, params)
                    results = cursor.fetchall()
                    # Convert RealDictRow to regular dict for compatibility
                    return [dict(row) for row in results]
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            self.logger.error(f"Original query: {query}")
            self.logger.error(f"Converted query: {self._convert_query_placeholders(query) if query else 'None'}")
            self.logger.error(f"Params: {params}")
            raise
    
    def execute_insert(self, query: str, params: tuple = None) -> Optional[int]:
        """Execute an INSERT query and return the number of affected rows"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Convert ? placeholders to PostgreSQL %s format
                    pg_query = self._convert_query_placeholders(query)
                    
                    # Ensure params is a tuple for psycopg2
                    if params is not None and not isinstance(params, tuple):
                        if isinstance(params, list):
                            params = tuple(params)
                        else:
                            params = (params,)
                    
                    self.logger.debug(f"Executing query: {pg_query}")
                    self.logger.debug(f"With parameters: {params}")
                    
                    cursor.execute(pg_query, params)
                    
                    # For our use case, we mainly care about successful insertion
                    # Return the number of affected rows instead of trying to get ID
                    affected_rows = cursor.rowcount
                    conn.commit()
                    return affected_rows
                    
        except Exception as e:
            self.logger.error(f"Insert execution failed: {e}")
            self.logger.error(f"Original query: {query}")
            self.logger.error(f"Converted query: {self._convert_query_placeholders(query) if query else 'None'}")
            self.logger.error(f"Params: {params}")
            self.logger.error(f"Params type: {type(params)}")
            raise
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an UPDATE query and return number of affected rows"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Convert ? placeholders to PostgreSQL %s format
                    pg_query = self._convert_query_placeholders(query)
                    
                    # Ensure params is a tuple for psycopg2
                    if params is not None and not isinstance(params, tuple):
                        if isinstance(params, list):
                            params = tuple(params)
                        else:
                            params = (params,)
                    
                    cursor.execute(pg_query, params)
                    affected_rows = cursor.rowcount
                    conn.commit()
                    return affected_rows
        except Exception as e:
            self.logger.error(f"Update execution failed: {e}")
            self.logger.error(f"Original query: {query}")
            self.logger.error(f"Converted query: {self._convert_query_placeholders(query) if query else 'None'}")
            self.logger.error(f"Params: {params}")
            raise
    
    def execute_delete(self, query: str, params: tuple = None) -> int:
        """Execute a DELETE query and return number of affected rows"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Convert ? placeholders to PostgreSQL %s format
                    pg_query = self._convert_query_placeholders(query)
                    
                    # Ensure params is a tuple for psycopg2
                    if params is not None and not isinstance(params, tuple):
                        if isinstance(params, list):
                            params = tuple(params)
                        else:
                            params = (params,)
                    
                    cursor.execute(pg_query, params)
                    affected_rows = cursor.rowcount
                    conn.commit()
                    return affected_rows
        except Exception as e:
            self.logger.error(f"Delete execution failed: {e}")
            self.logger.error(f"Original query: {query}")
            self.logger.error(f"Converted query: {self._convert_query_placeholders(query) if query else 'None'}")
            self.logger.error(f"Params: {params}")
            raise
    
    def execute_batch_insert(self, query: str, data: List[tuple]) -> int:
        """Execute batch insert for multiple records"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Convert ? placeholders to PostgreSQL %s format
                    pg_query = self._convert_query_placeholders(query)
                    execute_values(cursor, pg_query, data, template=None, page_size=100)
                    affected_rows = cursor.rowcount
                    conn.commit()
                    return affected_rows
        except Exception as e:
            self.logger.error(f"Batch insert execution failed: {e}")
            self.logger.error(f"Query: {query}")
            self.logger.error(f"Data sample: {data[:2] if data else 'No data'}")
            raise
    
    def execute_transaction(self, queries: List[Tuple[str, tuple]]) -> bool:
        """Execute multiple queries in a transaction"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    for query, params in queries:
                        # Convert ? placeholders to PostgreSQL %s format
                        pg_query = self._convert_query_placeholders(query)
                        
                        # Ensure params is a tuple for psycopg2
                        if params is not None and not isinstance(params, tuple):
                            if isinstance(params, list):
                                params = tuple(params)
                            else:
                                params = (params,)
                        
                        cursor.execute(pg_query, params)
                    conn.commit()
                    return True
        except Exception as e:
            self.logger.error(f"Transaction execution failed: {e}")
            raise
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get information about table columns"""
        try:
            query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = %s 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
            """
            return self.execute_query(query, (table_name,))
        except Exception as e:
            self.logger.error(f"Failed to get table info for {table_name}: {e}")
            return []
    
    def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        try:
            query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
            """
            result = self.execute_query(query, (table_name,))
            return result[0]['exists'] if result else False
        except Exception as e:
            self.logger.error(f"Failed to check if table {table_name} exists: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {}
            
            # Get table row counts - Updated table names to match schema
            tables = ['deals', 'deal_activities', 'crmteam', 'sentiment_analysis']
            for table in tables:
                if self.check_table_exists(table):
                    count_query = f'SELECT COUNT(*) as count FROM "{table}";'
                    result = self.execute_query(count_query)
                    stats[f"{table}_count"] = result[0]['count'] if result else 0
                else:
                    stats[f"{table}_count"] = 0
            
            # Get database size
            size_query = """
            SELECT pg_size_pretty(pg_database_size(current_database())) as db_size;
            """
            result = self.execute_query(size_query)
            stats['database_size'] = result[0]['db_size'] if result else 'Unknown'
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get general database information for compatibility"""
        try:
            info = {}
            
            # Database version
            version_query = "SELECT version()"
            version_result = self.execute_query(version_query)
            info['version'] = version_result[0]['version'] if version_result else 'Unknown'
            
            # Current database
            db_query = "SELECT current_database()"
            db_result = self.execute_query(db_query)
            info['current_database'] = db_result[0]['current_database'] if db_result else 'Unknown'
            
            # Tables count
            tables_query = """
            SELECT COUNT(*) as table_count 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            """
            tables_result = self.execute_query(tables_query)
            info['table_count'] = tables_result[0]['table_count'] if tables_result else 0
            
            # Get table names
            table_names_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
            """
            tables_list = self.execute_query(table_names_query)
            info['tables'] = [row['table_name'] for row in tables_list]
            
            return info
            
        except Exception as e:
            self.logger.error(f"Database info retrieval failed: {e}")
            return {}
    
    def truncate_table(self, table_name: str, cascade: bool = False) -> bool:
        """Truncate a table"""
        try:
            cascade_clause = "CASCADE" if cascade else ""
            query = f'TRUNCATE TABLE "{table_name}" {cascade_clause}'
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                conn.commit()
            
            self.logger.info(f"Table {table_name} truncated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Table truncation failed for {table_name}: {e}")
            return False
    
    def bulk_insert(self, table_name: str, columns: List[str], data: List[Tuple], 
                   on_conflict: str = None) -> int:
        """Perform bulk insert operation"""
        try:
            # Build the query with proper column quoting
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join([f'"{col}"' for col in columns])
            
            query = f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'
            
            if on_conflict:
                query += f' {on_conflict}'
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.executemany(query, data)
                    affected_rows = cursor.rowcount
                conn.commit()
                return affected_rows
                    
        except Exception as e:
            self.logger.error(f"Bulk insert failed for table {table_name}: {e}")
            raise
    
    def create_backup(self, backup_path: str = None) -> str:
        """Create a database backup using pg_dump"""
        import subprocess
        from datetime import datetime
        
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_persian_crm_{timestamp}.sql"
            
            # Prepare pg_dump command
            cmd = [
                'pg_dump',
                '-h', self.db_config['host'],
                '-p', str(self.db_config['port']),
                '-U', self.db_config['user'],
                '-d', self.db_config['database'],
                '-f', backup_path,
                '--verbose'
            ]
            
            # Set password via environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            # Execute pg_dump
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Database backup created successfully: {backup_path}")
                return backup_path
            else:
                self.logger.error(f"Backup failed: {result.stderr}")
                raise Exception(f"pg_dump failed: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Failed to create database backup: {e}")
            raise
    
    def close(self):
        """Close all connections in the pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            self.logger.info("Database connection pool closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Factory function to create database manager
def create_database_manager() -> DatabaseManager:
    """Factory function to create database manager instance"""
    return DatabaseManager()

# Singleton pattern for global access
_db_manager_instance = None

def get_database_manager() -> DatabaseManager:
    """Get singleton database manager instance"""
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = create_database_manager()
    return _db_manager_instance


# Test function for compatibility
def test_database_connection():
    """Test function to verify database connection"""
    try:
        print("Testing database connection...")
        db = DatabaseManager()
        
        if not db.test_connection():
            print("❌ Database connection test failed")
            return False
        
        print("✅ Database connection successful")
        
        # Test basic operations
        info = db.get_database_info()
        print(f"Database: {info.get('current_database', 'Unknown')}")
        print(f"Tables: {info.get('table_count', 0)}")
        
        if info.get('tables'):
            print("Available tables:", ', '.join(info['tables']))
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    # Run connection test
    test_database_connection()