
"""
Pipeline module for the RAG system.
"""
from ollama_client.llm import query_ollama
from chroma.chroma import query_chromadb

def rag_pipeline(query_text):
    """
    Perform Retrieval-Augmented Generation (RAG) by combining ChromaDB and Ollama.
    
    Args:
        query_text (str): The input query.
    
    Returns:
        str: The generated response from Ollama augmented with retrieved context.
    """
    try:
        retrieved_docs, metadata = query_chromadb(query_text)
        context = " ".join(retrieved_docs[0]) if retrieved_docs else "No relevant documents found."

        # Step 2: Send the query along with the context to Ollama
        augmented_prompt = f"Context: {context}\n\nQuestion: {query_text}\nAnswer:"
        print("######## Augmented Prompt ########")
        print(augmented_prompt)

        response = query_ollama(augmented_prompt)
        return response
    except Exception as e:
        print(f"Error in RAG pipeline: {e}")
        return f"I'm sorry, there was an error processing your query: {str(e)}"
