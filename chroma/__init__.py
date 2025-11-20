
"""
This file creates proper Python package exports to make imports work correctly
in a modular Docker environment.
"""


from .chroma import query_chromadb, collection, llm_model
