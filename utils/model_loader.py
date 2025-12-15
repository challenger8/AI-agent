"""
utils/model_loader.py
---------------------
Utility for consistent model loading across services.

DRY: Consolidates duplicate environment setup and retry logic
found in embedding_service.py, batch_embedding_service.py, and sentiment_service.py
"""

import os
import asyncio
import logging
from typing import Callable, Optional, Any, TypeVar
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ModelLoader:
    """
    Utility class for model loading with consistent environment setup.

    DRY: Eliminates duplicate environment variable setup across 3 services:
    - services/embedding_service.py
    - services/batch_embedding_service.py
    - services/sentiment_service.py
    """

    @staticmethod
    def setup_cpu_only_environment() -> None:
        """
        Set up environment for CPU-only model execution.

        DRY: Consolidates identical environment setup from:
        - embedding_service.py:43-45
        - batch_embedding_service.py:93-94

        This disables:
        - TensorFlow logging (reduces noise)
        - Tokenizers parallelism (prevents deadlocks)
        - CUDA devices (forces CPU execution)
        """
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF warnings
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'  # Prevent deadlocks
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU only
        logger.debug("Environment configured for CPU-only model execution")

    @staticmethod
    def setup_minimal_logging() -> None:
        """
        Set up minimal logging for ML libraries.

        Reduces noise from transformers, sentence_transformers, etc.
        """
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        logger.debug("Minimal logging configured for ML libraries")

    @staticmethod
    async def load_with_retry(
        loader_func: Callable[[], T],
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        error_msg: str = "Model loading failed"
    ) -> Optional[T]:
        """
        Load model with exponential backoff retry logic.

        Args:
            loader_func: Async function that loads the model
            max_retries: Maximum number of retry attempts
            delay: Initial delay between retries (seconds)
            backoff: Multiplier for delay on each retry
            error_msg: Error message prefix

        Returns:
            Loaded model or None on failure

        Example:
            ```python
            async def load_my_model():
                return SentenceTransformer('model-name')

            model = await ModelLoader.load_with_retry(load_my_model)
            ```
        """
        current_delay = delay
        last_error = None

        for attempt in range(max_retries):
            try:
                logger.info(f"Loading model (attempt {attempt + 1}/{max_retries})...")

                # Call the loader function
                if asyncio.iscoroutinefunction(loader_func):
                    result = await loader_func()
                else:
                    result = loader_func()

                logger.info("✅ Model loaded successfully")
                return result

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Model loading attempt {attempt + 1} failed: {e}"
                )

                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {current_delay:.1f}s...")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        # All retries exhausted
        logger.error(f"{error_msg}: {last_error}")
        return None

    @staticmethod
    def check_already_loaded(
        model: Any,
        model_name: str = "Model"
    ) -> bool:
        """
        Check if model is already loaded.

        DRY: Consolidates the "already loaded" check pattern from:
        - batch_embedding_service.py:82-84

        Args:
            model: Model instance (None if not loaded)
            model_name: Name for logging

        Returns:
            True if model already loaded
        """
        if model is not None:
            logger.info(f"{model_name} already loaded")
            return True
        return False


def setup_model_environment(cpu_only: bool = True) -> Callable:
    """
    Decorator to set up model environment before function execution.

    Args:
        cpu_only: If True, force CPU-only execution

    Example:
        ```python
        @setup_model_environment(cpu_only=True)
        async def load_model(self):
            # Environment already configured for CPU
            return SentenceTransformer('model-name', device='cpu')
        ```
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if cpu_only:
                ModelLoader.setup_cpu_only_environment()
            else:
                ModelLoader.setup_minimal_logging()

            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if cpu_only:
                ModelLoader.setup_cpu_only_environment()
            else:
                ModelLoader.setup_minimal_logging()
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Convenience functions for common patterns
def setup_cpu_env():
    """Shorthand for CPU-only environment setup"""
    ModelLoader.setup_cpu_only_environment()


def setup_minimal_env():
    """Shorthand for minimal logging setup"""
    ModelLoader.setup_minimal_logging()
