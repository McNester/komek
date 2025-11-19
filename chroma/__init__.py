
"""
This file creates proper Python package exports to make imports work correctly
in a modular Docker environment.
"""

# Re-export the modules and functions that need to be used elsewhere
from .chroma import query_chromadb, collection, llm_model
