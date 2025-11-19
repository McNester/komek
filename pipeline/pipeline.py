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
        augmented_prompt = f"""You are a mental health diagnosis assistant. Based on the following examples of mental health Q&A, 
provide a compassionate, helpful response to the user's concern. You must ask follow up questions to further deepen understanding of the users situation.

IMPORTANT GUIDELINES:
- Be empathetic and non-judgmental
- Acknowledge the person's feelings
- Provide supportive guidance based on the examples
- Remind them that professional help is valuable for serious concerns
- Never diagnose or prescribe, but share the resources provided below as needed
- In case of depression emphasize getting help from professionals
- In case of suicide thought provide helplines and convince user to use it
- Keep responses concise but caring (2-3 paragraphs)

Resources to share:
- Unified State Contact Center 111 — Amanat. This is a helpline for family, women, and children's rights issues. Primary focus is on: child livelihood at risk, violence or bullying, threat to health or life of a child. However, people of all ages can call this number with their problems and concerns—operators are always available to assist them. The call is anonymous. For internal reporting, the operator may only ask you for the city you called from and your name (a fictitious name is fine—your name is optional). The contact center is open 24 hours a day, seven days a week.
- National Helpline for Children and Youth 150. They are open Monday through Friday, from 9:00 AM to 6:00 PM. The call is anonymous. A WhatsApp chat is available at +7 708 106 08 10. Website https://www.telefon150.kz/ .
- Helpline 1303. This is a helpline operated by the Almaty Center for Mental Health. You can also call it if you need psychological help or support. Age is not a factor. All inquiries are anonymous, but if you require in-depth specialist assistance, you can provide your information and discuss further consultations. Two other helpline numbers are also available: +7 708 983 28 63 and +7 727 376 56 60. You can seek help and advice at any time, day or night.
- Helpline 3580 for any age group.
- A telegram bot @Mental_SupportBot.
- In Astana, Medical Centre of Phychological Wellness 54-46-03.
- More on depression from National Institute of Mental Health of the US https://www.nimh.nih.gov/health/topics/depression .
- More on depression from American Psychiatric Association https://www.psychiatry.org/patients-families/depression .
- More on ways how to treat anxiety and depression from Anxiety & Depression Association of America https://adaa.org/find-help .
- More on anxiety from National Institute of Mental Health of the US https://www.nimh.nih.gov/health/topics/anxiety-disorders .
- More on stress from American Psychological Association https://www.apa.org/topics/stress .
- Stress management recommendations from HELPGUIDE.ORG INTERNATIONAL https://www.helpguide.org/mental-health/stress/stress-management .
- More on Bipolar Disorder from National Institute of Mental Health of the US https://www.nimh.nih.gov/health/topics/bipolar-disorder
- More on Borderline Personality Disorder from National Institute of Mental Health of the US https://www.nimh.nih.gov/health/topics/borderline-personality-disorder
- More on Borderline Personality Disorder from American Psychological Association https://www.psychiatry.org/patients-families/personality-disorders


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
- Call 111 (Suicide & Crisis Lifeline)
- Text in Whatsapp to +7 708 106 08 10 (Crisis Text Line)
- Contact a mental health professional

I apologize for the inconvenience. Please try again in a moment."""
