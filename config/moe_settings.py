"""
config/moe_settings.py
---------------------
REFACTORED: Backward compatibility wrapper

This file now imports from the modular config/moe/ package.
All logic has been split into focused modules:
- config/moe/config.py: Data structures
- config/moe/validator.py: Validation logic
- config/moe/accessor.py: Accessor methods
- config/moe/settings.py: Facade

For backward compatibility, we re-export MoESettings here.
"""

# Import the refactored modular components
from config.moe import MoESettings, MoEConfig, MoEConfigValidator, MoEConfigAccessor

# Re-export for backward compatibility
__all__ = ['MoESettings', 'MoEConfig', 'MoEConfigValidator', 'MoEConfigAccessor']

# Note: Old code can still do:
#   from config.moe_settings import MoESettings
# and it will work exactly as before.
