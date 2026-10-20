import sys
from unittest.mock import MagicMock

# Mock tkinter before any imports
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.Menu'] = MagicMock()
