import sys
from unittest.mock import MagicMock

# This test environment does not have tkinter installed (ModuleNotFoundError).
# Mock it only as a fallback when the real module is genuinely missing, never
# overriding an actual installation. The ui.py module imports tkinter at the
# top level, so we must mock it before test collection.
try:
    import tkinter  # noqa: F401
except ImportError:
    sys.modules['tkinter'] = MagicMock()
