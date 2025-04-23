import os
from dotenv import load_dotenv 
load_dotenv()
from google import genai
from google.genai import types
from app.schemas.smart_search import SmartSearchFields
from app.db.cache_service import CacheService

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("Missing API key: set GEMINI_API_KEY or GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

async def run_smart_search(prompt: str) -> SmartSearchFields:
    players = await CacheService.get_all_cached_responses("players")
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-04-17",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction="""
            <person>
                You are a very good soccer player scout that works on the LB Sports Agency. You are great on getting club requests and matching them with the agency player database.
            </person>
            <goal>
                Check the players list database and provide 5 recommendations.
                According to the user (club) input provided, evaluate the information and provide the best search parameters to be used to find the ideal set of applicable players that we got!
            </goal>
            <instructions>
                Consider the players and provide me a list of 5 players that best macth the club request. Example:
                (name) - (position) - (market value) - (contract expire date)
                Also provide the ideal search for the player to match the club requirements. Expand the search ideas and provide other search fields that could be a good match for the club request. This will be a text response as an advise providing the fields and the reason for them. 
            </instructions>
            <player_data>
                """ + "\n".join(str(player) for player in players) + """
            </player_data>""",
            response_mime_type="application/json",
            response_schema=SmartSearchFields,
        ),
    )
    # Parse JSON response into Pydantic model
    return SmartSearchFields.model_validate_json(response.text)
