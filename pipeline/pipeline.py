"""
Pipeline module for the Mental Health Support RAG system.
"""
from ollama_client.llm import query_ollama
from chroma.chroma import query_chromadb

def rag_pipeline(query_text):
    """
    Perform Retrieval-Augmented Generation (RAG) for mental health support.
    
    This retrieves relevant mental health Q&A examples and uses them to provide
    supportive, informed responses.
    
    Args:
        query_text (str): The user's input/question.
    
    Returns:
        str: The generated supportive response from the LLM.
    """
    try:
        # Retrieve relevant mental health Q&A documents (get top 3 for better context)
        retrieved_docs, metadata = query_chromadb(query_text, n_results=3)
        
        # Combine retrieved documents into context
        if retrieved_docs and len(retrieved_docs[0]) > 0:
            context_parts = []
            for doc in retrieved_docs[0]:
                context_parts.append(doc)
            context = "\n\n---\n\n".join(context_parts)
        else:
            context = "No specific examples found, but I'm here to help."

        # Create an empathetic, professional prompt
        augmented_prompt = f"""You are a supportive mental health assistant. Based on the following examples of mental health Q&A, 
provide a compassionate, helpful response to the user's concern.

IMPORTANT GUIDELINES:
- Be empathetic and non-judgmental
- Acknowledge the person's feelings
- Provide supportive guidance based on the examples
- Remind them that professional help is valuable for serious concerns
- Never diagnose or prescribe
- Keep responses concise but caring (2-3 paragraphs)

Reference Examples:
{context}

User's Concern: {query_text}

Your Supportive Response:"""
        
        print("######## Mental Health Support Prompt ########")
        print(augmented_prompt)
        print("######## End Prompt ########")

        response = query_ollama(augmented_prompt)
        return response
        
    except Exception as e:
        print(f"Error in RAG pipeline: {e}")
        return """I understand you're reaching out for support. While I'm here to help, 
I'm experiencing a technical issue right now. 

If you're in immediate distress, please:
- Call 988 (Suicide & Crisis Lifeline)
- Text HOME to 741741 (Crisis Text Line)
- Contact a mental health professional

I apologize for the inconvenience. Please try again in a moment."""
