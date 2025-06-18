from openai import OpenAI

def chat_with_openai_like_llm(api_key, base_url):
    client = OpenAI(api_key=api_key, base_url=base_url)
    return client

