"""
Streamlit app entry point.
Run with: streamlit run app.py
"""

import sys
import os

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Now we can import from src
from src.main import main

if __name__ == "__main__":
    main()
