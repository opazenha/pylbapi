from fastapi import APIRouter, HTTPException
from app.services.smart_search import run_smart_search
from app.schemas.smart_search import SmartSearchFields

router = APIRouter()

@router.get(
    "/",
    response_model=SmartSearchFields,
    summary="Smart Search for Player Scouting",
    description="Generate search parameters based on a club's prompt using Gemini LLM.",
    tags=["smartsearch"],
)
async def smart_search(prompt: str):
    """
    Generate structured search fields from a club's description prompt using Gemini 2.5 Flash.
    """
    try:
        result = run_smart_search(prompt)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
