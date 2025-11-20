from langchain_ollama import OllamaEmbeddings, OllamaLLM

llm_model = "llama3.2"


def query_ollama(prompt):
    """
    Send a query to Ollama and retrieve the response.
    
    Args:
        prompt (str): The input prompt for Ollama.
    
    Returns:
        str: The response from Ollama.
    """
    llm = OllamaLLM(model=llm_model, base_url="http://host.docker.internal:11434")
    return llm.invoke(prompt)
