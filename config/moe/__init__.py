"""
config/moe/__init__.py
----------------------
Modular MoE configuration package

REFACTORED: Split MoESettings God Class into focused modules:
- config.py: Data structures only (dataclass)
- validator.py: Validation logic
- accessor.py: Configuration accessor methods
- settings.py: Facade for backward compatibility
"""

from .config import MoEConfig, load_moe_config
from .validator import MoEConfigValidator
from .accessor import MoEConfigAccessor

# Backward compatibility facade
from .settings import MoESettings

__all__ = [
    'MoEConfig',
    'load_moe_config',
    'MoEConfigValidator',
    'MoEConfigAccessor',
    'MoESettings',  # Backward compatible
]
