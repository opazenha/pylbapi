from typing import Optional

from fastapi import APIRouter, Depends

from app.schemas import clubs as schemas
from app.services.clubs.players import TransfermarktClubPlayers
from app.services.clubs.profile import TransfermarktClubProfile
from app.services.clubs.search import TransfermarktClubSearch
from app.db.cache_service import CacheService

router = APIRouter()


@router.get("/search/{club_name}", response_model=schemas.ClubSearch, response_model_exclude_none=True)
async def search_clubs(club_name: str, page_number: Optional[int] = 1) -> dict:
    # Search endpoints don't use caching
    tfmkt = TransfermarktClubSearch(query=club_name, page_number=page_number)
    found_clubs = tfmkt.search_clubs()
    return found_clubs


@router.get("/{club_id}/profile", response_model=schemas.ClubProfile, response_model_exclude_defaults=True)
async def get_club_profile(club_id: str) -> dict:
    # Check cache first
    cached_data = await CacheService.get_cached_response("clubs", club_id)
    # Check if cache exists and is not older than 1 day
    if cached_data and not await CacheService.is_cache_expired(cached_data):
        return cached_data
        
    # If not in cache or cache is expired, fetch from the API
    tfmkt = TransfermarktClubProfile(club_id=club_id)
    club_profile = tfmkt.get_club_profile()
    
    # Cache the result
    if club_profile:
        data = club_profile.dict() if hasattr(club_profile, "dict") else club_profile
        await CacheService.cache_response("clubs", data)
        
    return club_profile


@router.get("/{club_id}/players", response_model=schemas.ClubPlayers, response_model_exclude_defaults=True)
async def get_club_players(club_id: str, season_id: Optional[str] = None) -> dict:
    # Create a unique cache key including season_id if provided
    cache_key = f"{club_id}_{season_id}" if season_id else club_id
    
    # Check cache first
    cached_data = await CacheService.get_cached_response("club_players", cache_key)
    # Check if cache exists and is not older than 1 day
    if cached_data and not await CacheService.is_cache_expired(cached_data):
        return cached_data
        
    # If not in cache or cache is expired, fetch from the API
    tfmkt = TransfermarktClubPlayers(club_id=club_id, season_id=season_id)
    club_players = tfmkt.get_club_players()
    
    # Cache the result
    if club_players:
        # Check if club_players is a Pydantic model or already a dict
        data = club_players.dict() if hasattr(club_players, "dict") else club_players
        # Use our custom cache key if we used one
        if season_id:
            data["id"] = cache_key
        await CacheService.cache_response("club_players", data)
        
    return club_players
