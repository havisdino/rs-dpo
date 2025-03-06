from openai import AzureOpenAI
import os


# azure configs
API_KEY = os.environ["API_KEY"]
API_VERSION = "2024-10-21"
AZURE_ENDPOINT = "https://batch-4o.openai.azure.com/"

# model names
GPT4O = "gpt-4o-std"
GPT4O_MINI = "gpt-4o-mini-std"
O3_MINI = "o3-mini"

# generation configs
TEMPERATURE = 0.0
TOP_P = 0.9
MAX_TOKENS = 1024

def get_completion(
    prompt,
    system_prompt=None,
    model=GPT4O,
    temperature=TEMPERATURE,
    top_p=TOP_P,
    max_tokens=MAX_TOKENS,
    api_key=API_KEY,
    api_version=API_VERSION,
    azure_endpoint=AZURE_ENDPOINT,
):
    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=azure_endpoint,
    )
    
    messages = []
    if system_prompt is not None:
        messages.append({"role": "system", "content": system_prompt})
        
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content