import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.db.database import Database
from app.db.cache_service import CacheService
from app.services.clubs.search import TransfermarktClubSearch
from app.services.clubs.players import TransfermarktClubPlayers
from app.services.players.profile import TransfermarktPlayerProfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("background_refresh")

class BackgroundRefreshService:
    """
    Service that periodically refreshes cached data in the background.
    It refreshes player profiles from all clubs at a controlled rate
    to avoid being blocked by the scraped website.
    """
    
    # Delay between scraping requests in seconds
    SCRAPE_DELAY = 10
    
    def __init__(self):
        """Initialize the refresh service."""
        self.is_running = False
        self.task = None
    
    async def start(self):
        """Start the background refresh service."""
        if self.is_running:
            logger.info("Background refresh service is already running")
            return
            
        self.is_running = True
        self.task = asyncio.create_task(self.refresh_loop())
        logger.info("Started background refresh service")
    
    async def stop(self):
        """Stop the background refresh service."""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped background refresh service")
    
    async def refresh_loop(self):
        """Main refresh loop that runs continuously."""
        while self.is_running:
            try:
                logger.info("Starting a new refresh cycle")
                await self.refresh_all_players()
                logger.info("Completed refresh cycle")
            except Exception as e:
                logger.error(f"Error in refresh cycle: {e}")
            
            # Wait a bit before starting a new cycle
            await asyncio.sleep(60)
    
    async def refresh_all_players(self):
        """Refresh all players from all clubs."""
        # Get all clubs first
        clubs = await self.get_all_clubs()
        
        if not clubs:
            logger.warning("No clubs found to refresh players from")
            return
            
        logger.info(f"Found {len(clubs)} clubs to process")
        
        # Process each club
        for club in clubs:
            try:
                await self.refresh_club_players(club["id"])
            except Exception as e:
                logger.error(f"Error refreshing players for club {club['id']}: {e}")
    
    async def get_all_clubs(self) -> List[Dict[str, Any]]:
        """Get all clubs from the database or scrape them if needed."""
        # Check if we have clubs in the database
        collection = await Database.get_collection("clubs")
        clubs = await collection.find({}).to_list(length=1000)
        
        if clubs:
            logger.info(f"Found {len(clubs)} clubs in the database")
            return clubs
            
        # If no clubs in database, scrape some popular leagues
        logger.info("No clubs in database, scraping popular leagues")
        club_ids = []
        
        # Scrape some popular leagues (English Premier League, La Liga, etc.)
        popular_leagues = ["GB1", "ES1", "L1", "IT1", "FR1"]
        
        for league_id in popular_leagues:
            tfmkt = TransfermarktClubSearch(query=league_id, page_number=1)
            clubs_data = tfmkt.search_clubs()
            
            if clubs_data and "results" in clubs_data:
                for club in clubs_data["results"]:
                    club_ids.append({"id": club["id"], "name": club["name"]})
            
            # Delay between requests
            await asyncio.sleep(self.SCRAPE_DELAY)
        
        return club_ids
    
    async def refresh_club_players(self, club_id: str):
        """Refresh all players from a specific club."""
        logger.info(f"Refreshing players for club: {club_id}")
        
        # Get the club's players
        tfmkt = TransfermarktClubPlayers(club_id=club_id)
        club_players_data = tfmkt.get_club_players()
        
        # Wait between requests
        await asyncio.sleep(self.SCRAPE_DELAY)
        
        if not club_players_data or "players" not in club_players_data:
            logger.warning(f"No players found for club {club_id}")
            return
            
        players = club_players_data["players"]
        logger.info(f"Found {len(players)} players for club {club_id}")
        
        # Refresh each player's profile
        for player in players:
            await self.refresh_player_profile(player["id"])
            
            # Wait between requests to avoid rate limiting
            await asyncio.sleep(self.SCRAPE_DELAY)
    
    async def refresh_player_profile(self, player_id: str):
        """Refresh a player's profile data."""
        logger.info(f"Refreshing player profile: {player_id}")
        
        try:
            # Check if we have this player cached and if it's an LB player
            cached_player = await CacheService.get_cached_response("players", player_id)
            is_lb_player = cached_player.get("isLbPlayer", False) if cached_player else False
            
            # Fetch fresh player data
            tfmkt = TransfermarktPlayerProfile(player_id=player_id)
            player_data = tfmkt.get_player_profile()
            
            if not player_data:
                logger.warning(f"Could not fetch data for player {player_id}")
                return
                
            # Prepare data for caching
            data = player_data.dict() if hasattr(player_data, "dict") else player_data
            
            # Preserve the isLbPlayer flag if it was set
            if is_lb_player:
                data["isLbPlayer"] = True
                
            # Cache the refreshed data
            await CacheService.cache_response("players", data)
            logger.info(f"Successfully refreshed player {player_id}")
            
        except Exception as e:
            logger.error(f"Error refreshing player {player_id}: {e}")

# Create a singleton instance
background_refresh_service = BackgroundRefreshService()
