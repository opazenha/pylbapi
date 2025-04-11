from typing import Optional

from fastapi import APIRouter, Depends

from app.schemas import players as schemas
from app.services.players.achievements import TransfermarktPlayerAchievements
from app.services.players.injuries import TransfermarktPlayerInjuries
from app.services.players.jersey_numbers import TransfermarktPlayerJerseyNumbers
from app.services.players.market_value import TransfermarktPlayerMarketValue
from app.services.players.profile import TransfermarktPlayerProfile
from app.services.players.search import TransfermarktPlayerSearch
from app.services.players.stats import TransfermarktPlayerStats
from app.services.players.transfers import TransfermarktPlayerTransfers
from app.db.cache_service import CacheService

router = APIRouter()


@router.get("/search/{player_name}", response_model=schemas.PlayerSearch, response_model_exclude_none=True)
async def search_players(player_name: str, page_number: Optional[int] = 1):
    # Search endpoints don't use caching
    tfmkt = TransfermarktPlayerSearch(query=player_name, page_number=page_number)
    found_players = tfmkt.search_players()
    return found_players


@router.get("/{player_id}/profile", response_model=schemas.PlayerProfile, response_model_exclude_none=True)
async def get_player_profile(player_id: str, isLbPlayer: bool = False):
    # Check cache first
    cached_data = await CacheService.get_cached_response("players", player_id)
    # Check if cache exists and is not older than 1 day
    if cached_data and not await CacheService.is_cache_expired(cached_data):
        # If we're updating the isLbPlayer flag, update the cached record
        if isLbPlayer != cached_data.get("isLbPlayer", False):
            cached_data["isLbPlayer"] = isLbPlayer
            await CacheService.cache_response("players", cached_data)
        return cached_data
        
    # If not in cache or cache is expired, fetch from the API
    tfmkt = TransfermarktPlayerProfile(player_id=player_id)
    player_info = tfmkt.get_player_profile()
    
    # Cache the result
    if player_info:
        data = player_info.dict() if hasattr(player_info, "dict") else player_info
        # Add the LB player flag
        data["isLbPlayer"] = isLbPlayer
        await CacheService.cache_response("players", data)
        
    return player_info


@router.get("/{player_id}/market_value", response_model=schemas.PlayerMarketValue, response_model_exclude_none=True)
async def get_player_market_value(player_id: str):
    # Check cache first
    cached_data = await CacheService.get_cached_response("player_market_values", player_id)
    # Check if cache exists and is not older than 1 day
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


@router.get("/{player_id}/transfers", response_model=schemas.PlayerTransfers, response_model_exclude_none=True)
async def get_player_transfers(player_id: str):
    # Check cache first
    cached_data = await CacheService.get_cached_response("player_transfers", player_id)
    # Check if cache exists and is not older than 1 day
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


@router.get("/{player_id}/jersey_numbers", response_model=schemas.PlayerJerseyNumbers, response_model_exclude_none=True)
async def get_player_jersey_numbers(player_id: str):
    # Check cache first
    cached_data = await CacheService.get_cached_response("player_jersey_numbers", player_id)
    # Check if cache exists and is not older than 1 day
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


@router.get("/{player_id}/stats", response_model=schemas.PlayerStats, response_model_exclude_none=True)
async def get_player_stats(player_id: str):
    # Check cache first
    cached_data = await CacheService.get_cached_response("player_stats", player_id)
    # Check if cache exists and is not older than 1 day
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


@router.get("/{player_id}/injuries", response_model=schemas.PlayerInjuries, response_model_exclude_none=True)
async def get_player_injuries(player_id: str, page_number: Optional[int] = 1):
    # Check cache first - we include page number in the cache key
    cache_key = f"{player_id}_{page_number}"
    cached_data = await CacheService.get_cached_response("player_injuries", cache_key)
    # Check if cache exists and is not older than 1 day
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


@router.get("/{player_id}/achievements", response_model=schemas.PlayerAchievements, response_model_exclude_none=True)
async def get_player_achievements(player_id: str):
    # Check cache first
    cached_data = await CacheService.get_cached_response("player_achievements", player_id)
    # Check if cache exists and is not older than 1 day
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
