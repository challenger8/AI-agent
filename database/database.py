"""
database.py
-----------
PostgreSQL database module for Persian Deal Analyzer with SSH tunneling support
Based on working SSH tunnel implementation
"""

import pandas as pd
from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
from contextlib import contextmanager
import os
import time
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class SSHConfig:
    """SSH configuration for tunneling - reads from env only."""
    host: str
    port: int
    username: str
    password: str
    
    @classmethod
    def from_env(cls) -> 'SSHConfig':
        """Create SSH config from environment variables only."""
        return cls(
            host=os.getenv('TARGET_HOST'),
            port=int(os.getenv('SSH_TARGET_PORT')),
            username=os.getenv('SSH_TARGET_USER'),
            password=os.getenv('SSH_TARGET_PASSWORD')
        )

@dataclass
class DatabaseConfig:
    """Database configuration class - reads from env only."""
    host: str
    port: int
    database: str
    username: str
    password: str
    use_ssh_tunnel: bool
    # SQLAlchemy pool settings
    pool_size: int = 5
    max_overflow: int = 10
    pool_pre_ping: bool = True
    pool_recycle: int = 3600
    ssh_config: Optional[SSHConfig] = None
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create config from environment variables only."""
        use_ssh = os.getenv('USE_SSH_TUNNEL', '').lower() == 'true'
        ssh_config = SSHConfig.from_env() if use_ssh else None
        
        return cls(
            host='localhost',  # Always localhost when using SSH tunnel
            port=5433,  # Local tunnel port (will be set by tunnel manager)
            database=os.getenv('TARGET_DB'),
            username=os.getenv('TARGET_USER'),
            password=os.getenv('TARGET_PASSWORD'),
            use_ssh_tunnel=use_ssh,
            ssh_config=ssh_config
        )
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string."""
        return f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class DatabaseManager:
    """PostgreSQL database manager with SSH tunnel support using sshtunnel library."""
    
    def __init__(self, config: DatabaseConfig = None):
        """Initialize database manager with configuration."""
        self.config = config or DatabaseConfig.from_env()
        self.engine: Optional[Engine] = None
        self.metadata = MetaData()
        self._column_mappings: Dict[str, List[str]] = {}
        self.tunnel = None
        
    def _initialize_engine(self):
        """Initialize SQLAlchemy engine with connection pooling."""
        try:
            self.engine = create_engine(
                self.config.connection_string,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_pre_ping=self.config.pool_pre_ping,
                pool_recycle=self.config.pool_recycle,
                echo=False  # Set to True for SQL query logging
            )
            logger.info(f"Database engine initialized for {self.config.database}")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
    
    def setup_connection(self) -> bool:
        """Setup database connection with SSH tunnel if needed."""
        try:
            # Start SSH tunnel if configured
            if self.config.use_ssh_tunnel and self.config.ssh_config:
                logger.info("Setting up SSH tunnel...")
                
                try:
                    from sshtunnel import SSHTunnelForwarder
                except ImportError:
                    logger.error("sshtunnel library not installed. Install with: pip install sshtunnel")
                    return False
                
                # Create SSH tunnel using the working configuration
                self.tunnel = SSHTunnelForwarder(
                    (self.config.ssh_config.host, self.config.ssh_config.port),
                    ssh_username=self.config.ssh_config.username,
                    ssh_password=self.config.ssh_config.password,
                    remote_bind_address=('localhost', 5423),  # PostgreSQL port on remote server
                    local_bind_address=('localhost', 5433),   # Local port for tunnel
                    logger=logger
                )
                
                # Start the tunnel
                self.tunnel.start()
                logger.info(f"SSH tunnel established on local port 5433")
                
                # Wait for tunnel to be ready
                time.sleep(1)
                
                # Update config to use tunnel
                self.config.host = 'localhost'
                self.config.port = 5433
                
            # Initialize database engine
            self._initialize_engine()
            
            # Test database connection
            if self.test_connection():
                logger.info("Database connection successful")
                return True
            else:
                logger.error("Database connection failed")
                return False
                
        except Exception as e:
            logger.error(f"Error setting up connection: {e}")
            return False
    
    def set_column_mappings(self, mappings: Dict[str, List[str]]):
        """Set column mappings for tables."""
        self._column_mappings = mappings
        logger.info(f"Column mappings set for {len(mappings)} tables")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        connection = None
        try:
            connection = self.engine.connect()
            yield connection
        except SQLAlchemyError as e:
            logger.error(f"Database connection error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                connection.close()
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_connection() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def list_tables(self) -> List[str]:
        """List all tables in the database."""
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            logger.info(f"Found {len(tables)} tables in database")
            return tables
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return []
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """Execute custom SQL query and return DataFrame."""
        try:
            with self.get_connection() as conn:
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
            
            logger.info(f"Query executed successfully, returned {len(df)} rows")
            return df
            
        except SQLAlchemyError as e:
            logger.error(f"Database error executing query: {e}")
            raise DatabaseError(f"Query execution failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            raise DatabaseError(f"Unexpected query error: {e}")
    
    def execute_non_query(self, query: str, params: Optional[Dict] = None) -> int:
        """Execute INSERT, UPDATE, DELETE query."""
        try:
            with self.get_connection() as conn:
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                conn.commit()
                affected_rows = result.rowcount
                logger.info(f"Query executed, {affected_rows} rows affected")
                return affected_rows
                
        except SQLAlchemyError as e:
            logger.error(f"Database error executing non-query: {e}")
            raise DatabaseError(f"Non-query execution failed: {e}")
    
    def close(self):
        """Close database engine and SSH tunnel."""
        try:
            # Close database engine
            if self.engine:
                self.engine.dispose()
                logger.info("Database engine closed")
            
            # Close SSH tunnel
            if self.tunnel:
                self.tunnel.stop()
                logger.info("SSH tunnel closed")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


class DatabaseError(Exception):
    """Custom database error class."""
    pass


def create_database_manager(config: Optional[DatabaseConfig] = None) -> DatabaseManager:
    """Factory function to create DatabaseManager instance."""
    return DatabaseManager(config)


if __name__ == "__main__":
    """Test the database connection."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.warning("python-dotenv not installed, using system environment variables")
    
    # Create and test database manager
    db = create_database_manager()
    
    if db.setup_connection():
        print("Database connection successful")
        tables = db.list_tables()
        print(f"Found tables: {tables}")
    else:
        print("Database connection failed")
    
    db.close()