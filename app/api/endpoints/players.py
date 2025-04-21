from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas import players as schemas
from app.schemas.player_registration import PlayerRegistration
from app.services.players.achievements import TransfermarktPlayerAchievements
from app.services.players.injuries import TransfermarktPlayerInjuries
from app.services.players.jersey_numbers import TransfermarktPlayerJerseyNumbers
from app.services.players.market_value import TransfermarktPlayerMarketValue
from app.services.players.profile import TransfermarktPlayerProfile
from app.services.players.search import TransfermarktPlayerSearch
from app.services.players.stats import TransfermarktPlayerStats
from app.services.players.transfers import TransfermarktPlayerTransfers
from app.db.cache_service import CacheService
from app.db.database import Database
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

async def ensure_partner_from_agent(player_info):
    """
    Extract agent from player_info and ensure unique partner is added to MongoDB.
    Accepts dict or Pydantic model.
    """
    data = player_info.dict() if hasattr(player_info, "dict") else player_info
    agent = data.get("agent")
    if agent and agent.get("name"):
        partner_data = {
            "name": agent["name"],
            "transfermarktUrl": agent.get("url"),
            "notes": ""
        }
        await Database.find_or_create("partners", {"name": agent["name"]}, partner_data)

async def check_if_lb_player(player_info) -> bool:
    """
    Check if the agency scraped on from Transfermarkt is LB SPORTS COMPANY and return bollean.
    """
    data = player_info.dict() if hasattr(player_info, "dict") else player_info
    if data.get("agent").get("name") == "LB SPORTS COMPANY":
        return True
    return False

async def register_player(player_data: PlayerRegistration):
    """Register a player with additional metadata."""
    try:
        # 1. Fetch player data from Transfermarkt
        # transfermarktId is guaranteed to be set by the model validator
        player_id = player_data.transfermarktId
        
        logger.info(f"Fetching player data for ID: {player_id}")
        tfmkt = TransfermarktPlayerProfile(player_id=player_id)
        player_info = tfmkt.get_player_profile()
        
        if not player_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player with ID {player_id} not found on Transfermarkt"
            )
        
        # Ensure partner is added from agent
        await ensure_partner_from_agent(player_info)
        data = player_info.dict() if hasattr(player_info, "dict") else player_info
        # 2. Add custom fields and isLbPlayer flag
        data["youtubeUrl"] = player_data.youtubeUrl
        data["notes"] = player_data.notes
        data["partnerId"] = player_data.partnerId
        # Properly determine isLbPlayer using check_if_lb_player
        data["isLbPlayer"] = await check_if_lb_player(player_info)
        
        # 3. Save to MongoDB (cache)
        await CacheService.cache_response("players", data)
        
        return data
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        logger.error(f"Error registering player: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering player: {str(e)}"
        )


@router.post(
    "/",
    response_model=schemas.PlayerProfile,
    response_model_exclude_none=True,
    summary="Register a new player",
    description="""Register a player by Transfermarkt ID and add custom metadata.
    
    This endpoint will:
    1. Scrape the player data from Transfermarkt using the provided ID
    2. Add the custom fields (youtubeUrl, notes, partnerId)
    3. Save to MongoDB with isLbPlayer flag set to true
    4. Return the enriched player profile
    """,
    response_description="Enriched player profile with custom metadata",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Player successfully registered"},
        404: {"description": "Player not found on Transfermarkt"},
        422: {"description": "Validation error in request data"},
        500: {"description": "Server error during registration"}
    }
)
async def create_player(player_data: PlayerRegistration):
    return await register_player(player_data)


@router.get(
    "/search/{player_name}",
    response_model=schemas.PlayerSearch,
    response_model_exclude_none=True,
    summary="Search for players by name",
    description="Returns a list of players matching the search query. This endpoint is not cached.",
    response_description="List of players matching the search query"
)
async def search_players(
    player_name: str,
    page_number: Optional[int] = 1
):
    """
    Search for players by name.
    
    - **player_name**: Name or part of the name to search for
    - **page_number**: Optional page number for paginated results (default: 1)
    """
    # Search endpoints don't use caching
    tfmkt = TransfermarktPlayerSearch(query=player_name, page_number=page_number)
    found_players = tfmkt.search_players()
    return found_players


@router.get(
    "/{player_id}/profile",
    response_model=schemas.PlayerProfile,
    response_model_exclude_none=True,
    summary="Get player profile by ID",
    description="""
    Returns detailed information about a player, including:
    - Basic information (name, birth date, nationality)
    - Current club and contract details
    - League information
    - Market value
    - Agent information
    - Social media links
    
    The response is cached for 3 days to minimize scraping operations.
    """,
    response_description="Detailed player profile information"
)
async def get_player_profile(
    player_id: str,
    isLbPlayer: bool = False
):
    """
    Get detailed profile information for a specific player.
    
    - **player_id**: Transfermarkt player ID
    - **isLbPlayer**: Flag to mark if the player is part of the LB agency (default: False)
    """
    # Check cache first
    cached_data = await CacheService.get_cached_response("players", player_id)
    # Check if cache exists and is not expired
    if cached_data and not await CacheService.is_cache_expired(cached_data):
        # Always ensure isLbPlayer based on agent
        new_flag = await check_if_lb_player(cached_data)
        if new_flag != cached_data.get("isLbPlayer", False):
            cached_data["isLbPlayer"] = new_flag
            await CacheService.cache_response("players", cached_data)
        return cached_data
        
    # If not in cache or cache is expired, fetch from the API
    tfmkt = TransfermarktPlayerProfile(player_id=player_id)
    player_info = tfmkt.get_player_profile()

    # Ensure partner is added from agent
    await ensure_partner_from_agent(player_info)
    data = player_info.dict() if hasattr(player_info, "dict") else player_info
    # Determine isLbPlayer based on agent
    data["isLbPlayer"] = await check_if_lb_player(player_info)
    await CacheService.cache_response("players", data)

    return data

@router.delete(
    "/{player_id}/profile",
    response_model=schemas.PlayerProfile,
    summary="Delete player by player ID",
    description="Returns the player profile being deleted.",
    response_description="Playe profile information."
)
async def delete_player_profile(player_id: str):
    """
    Delete the player that holds the provided ID

    - **player_id**: Transfermarkt player ID
    """
    from fastapi import HTTPException
    from app.db.database import Database

    # Fetch the player profile first
    player = await Database.find_one("players", {"id": player_id})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    # Delete the player
    deleted = await Database.delete_one("players", {"id": player_id})
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete player")
    return player

@router.get(
    "/{player_id}/market_value",
    response_model=schemas.PlayerMarketValue,
    response_model_exclude_none=True,
    summary="Get player market value by ID",
    description="Returns the current market value of a player.",
    response_description="Player market value information"
)
async def get_player_market_value(
    player_id: str
):
    """
    Get the current market value of a specific player.
    
    - **player_id**: Transfermarkt player ID
    """
    # Check cache first
    cached_data = await CacheService.get_cached_response("player_market_values", player_id)
    # Check if cache exists and is not expired
    if cached_data and not await CacheService.is_cache_expired(cached_data):
        return cached_data
        
    # If not in cache or cache is expired, fetch from the API
    tfmkt = TransfermarktPlayerMarketValue(player_id=player_id)
    player_market_value = tfmkt.get_player_market_value()
    
    # Cache the result
    if player_market_value:
        data = player_market_value.dict() if hasattr(player_market_value, "dict") else player_market_value
        await CacheService.cache_response("player_market_values", data)
        
    return player_market_value


@router.get(
    "/{player_id}/transfers",
    response_model=schemas.PlayerTransfers,
    response_model_exclude_none=True,
    summary="Get player transfers by ID",
    description="Returns a list of transfers for a player.",
    response_description="List of player transfers"
)
async def get_player_transfers(
    player_id: str
):
    """
    Get a list of transfers for a specific player.
    
    - **player_id**: Transfermarkt player ID
    """
    # Check cache first
    cached_data = await CacheService.get_cached_response("player_transfers", player_id)
    # Check if cache exists and is not expired
    if cached_data and not await CacheService.is_cache_expired(cached_data):
        return cached_data
        
    # If not in cache or cache is expired, fetch from the API
    tfmkt = TransfermarktPlayerTransfers(player_id=player_id)
    player_transfers = tfmkt.get_player_transfers()
    
    # Cache the result
    if player_transfers:
        data = player_transfers.dict() if hasattr(player_transfers, "dict") else player_transfers
        await CacheService.cache_response("player_transfers", data)
        
    return player_transfers


@router.get(
    "/{player_id}/jersey_numbers",
    response_model=schemas.PlayerJerseyNumbers,
    response_model_exclude_none=True,
    summary="Get player jersey numbers by ID",
    description="Returns a list of jersey numbers for a player.",
    response_description="List of player jersey numbers"
)
async def get_player_jersey_numbers(
    player_id: str
):
    """
    Get a list of jersey numbers for a specific player.
    
    - **player_id**: Transfermarkt player ID
    """
    # Check cache first
    cached_data = await CacheService.get_cached_response("player_jersey_numbers", player_id)
    # Check if cache exists and is not expired
    if cached_data and not await CacheService.is_cache_expired(cached_data):
        return cached_data
        
    # If not in cache or cache is expired, fetch from the API
    tfmkt = TransfermarktPlayerJerseyNumbers(player_id=player_id)
    player_jerseynumbers = tfmkt.get_player_jersey_numbers()
    
    # Cache the result
    if player_jerseynumbers:
        data = player_jerseynumbers.dict() if hasattr(player_jerseynumbers, "dict") else player_jerseynumbers
        await CacheService.cache_response("player_jersey_numbers", data)
        
    return player_jerseynumbers


@router.get(
    "/{player_id}/stats",
    response_model=schemas.PlayerStats,
    response_model_exclude_none=True,
    summary="Get player stats by ID",
    description="Returns detailed statistics for a player.",
    response_description="Detailed player statistics"
)
async def get_player_stats(
    player_id: str
):
    """
    Get detailed statistics for a specific player.
    
    - **player_id**: Transfermarkt player ID
    """
    # Check cache first
    cached_data = await CacheService.get_cached_response("player_stats", player_id)
    # Check if cache exists and is not expired
    if cached_data and not await CacheService.is_cache_expired(cached_data):
        return cached_data
        
    # If not in cache or cache is expired, fetch from the API
    tfmkt = TransfermarktPlayerStats(player_id=player_id)
    player_stats = tfmkt.get_player_stats()
    
    # Cache the result
    if player_stats:
        data = player_stats.dict() if hasattr(player_stats, "dict") else player_stats
        await CacheService.cache_response("player_stats", data)
        
    return player_stats


@router.get(
    "/{player_id}/injuries",
    response_model=schemas.PlayerInjuries,
    response_model_exclude_none=True,
    summary="Get player injuries by ID",
    description="Returns a list of injuries for a player.",
    response_description="List of player injuries"
)
async def get_player_injuries(
    player_id: str,
    page_number: Optional[int] = 1
):
    """
    Get a list of injuries for a specific player.
    
    - **player_id**: Transfermarkt player ID
    - **page_number**: Optional page number for paginated results (default: 1)
    """
    # Check cache first - we include page number in the cache key
    cache_key = f"{player_id}_{page_number}"
    cached_data = await CacheService.get_cached_response("player_injuries", cache_key)
    # Check if cache exists and is not expired
    if cached_data and not await CacheService.is_cache_expired(cached_data):
        return cached_data
        
    # If not in cache or cache is expired, fetch from the API
    tfmkt = TransfermarktPlayerInjuries(player_id=player_id, page_number=page_number)
    players_injuries = tfmkt.get_player_injuries()
    
    # Cache the result
    if players_injuries:
        data = players_injuries.dict() if hasattr(players_injuries, "dict") else players_injuries
        data["id"] = cache_key  # Use our custom cache key
        await CacheService.cache_response("player_injuries", data)
        
    return players_injuries


@router.get(
    "/{player_id}/achievements",
    response_model=schemas.PlayerAchievements,
    response_model_exclude_none=True,
    summary="Get player achievements by ID",
    description="Returns a list of achievements for a player.",
    response_description="List of player achievements"
)
async def get_player_achievements(
    player_id: str
):
    """
    Get a list of achievements for a specific player.
    
    - **player_id**: Transfermarkt player ID
    """
    # Check cache first
    cached_data = await CacheService.get_cached_response("player_achievements", player_id)
    # Check if cache exists and is not expired
    if cached_data and not await CacheService.is_cache_expired(cached_data):
        return cached_data
        
    # If not in cache or cache is expired, fetch from the API
    tfmkt = TransfermarktPlayerAchievements(player_id=player_id)
    player_achievements = tfmkt.get_player_achievements()
    
    # Cache the result
    if player_achievements:
        data = player_achievements.dict() if hasattr(player_achievements, "dict") else player_achievements
        await CacheService.cache_response("player_achievements", data)
        
    return player_achievements
