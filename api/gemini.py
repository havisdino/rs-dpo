from google import genai
import os

API_KEY = os.environ["API_KEY"]

TEMPERATURE = 0.0
TOP_P = 0.9


def get_completion(prompt, model="gemini-2.0-pro-exp-02-05"):
    client = genai.Client(api_key=API_KEY)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            temperature=TEMPERATURE,
            topP=TOP_P,
        )
    )
    return response.text.strip()