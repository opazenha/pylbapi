from typing import Optional

from fastapi import APIRouter, Depends

from app.schemas import competitions as schemas
from app.services.competitions.clubs import TransfermarktCompetitionClubs
from app.services.competitions.search import TransfermarktCompetitionSearch
from app.db.cache_service import CacheService

router = APIRouter()


@router.get("/search/{competition_name}", response_model=schemas.CompetitionSearch)
async def search_competitions(competition_name: str, page_number: Optional[int] = 1):
    # Search endpoints don't use caching
    tfmkt = TransfermarktCompetitionSearch(query=competition_name, page_number=page_number)
    competitions = tfmkt.search_competitions()
    return competitions


@router.get("/{competition_id}/clubs", response_model=schemas.CompetitionClubs)
async def get_competition_clubs(competition_id: str, season_id: Optional[str] = None):
    # Create a unique cache key including season_id if provided
    cache_key = f"{competition_id}_{season_id}" if season_id else competition_id
    
    # Check cache first
    cached_data = await CacheService.get_cached_response("competitions", cache_key)
    if cached_data:
        return cached_data
        
    # If not in cache, fetch from the API
    tfmkt = TransfermarktCompetitionClubs(competition_id=competition_id, season_id=season_id)
    competition_clubs = tfmkt.get_competition_clubs()
    
    # Cache the result
    if competition_clubs:
        # Check if competition_clubs is a Pydantic model or already a dict
        data = competition_clubs.dict() if hasattr(competition_clubs, "dict") else competition_clubs
        # Use our custom cache key if we used one
        if season_id:
            data["id"] = cache_key
        await CacheService.cache_response("competitions", data)
        
    return competition_clubs
