from langchain_ollama import OllamaEmbeddings, OllamaLLM

llm_model = "llama2"


def query_ollama(prompt):
    """
    Send a query to Ollama and retrieve the response.
    
    Args:
        prompt (str): The input prompt for Ollama.
    
    Returns:
        str: The response from Ollama.
    """
    # llm = OllamaLLM(model=llm_model, base_url="http://172.17.0.2:11434")
    llm = OllamaLLM(model=llm_model, base_url="http://host.docker.internal:11434")
    # llm = OllamaLLM(model=llm_model, base_url="http://quizzical_grothendieck:11434")
    return llm.invoke(prompt)
