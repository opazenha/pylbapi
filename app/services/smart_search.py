import os
from dotenv import load_dotenv  # load .env into environment
load_dotenv()
from google import genai
from google.genai import types
from app.schemas.smart_search import SmartSearchFields

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("Missing API key: set GEMINI_API_KEY or GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

def run_smart_search(prompt: str) -> SmartSearchFields:
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-04-17",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction="You are a very good soccer player scout. You ae great on getting club requests and matching them with the player database you have. According to the user (club) input provided, evaluate the information and provide the best search parameters to be used to find the ideal set of applicable players that we got!",
            response_mime_type="application/json",
            response_schema=SmartSearchFields,
        ),
    )
    # Parse JSON response into Pydantic model
    return SmartSearchFields.model_validate_json(response.text)
