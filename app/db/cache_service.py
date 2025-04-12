from typing import Dict, Any, Optional, List, Union, Type
from datetime import datetime, timedelta

from app.db.database import Database
from pydantic import BaseModel

class CacheService:
    """Service for caching API responses in MongoDB."""
    
    # Cache expiration time in days
    CACHE_EXPIRATION_DAYS = 3
    
    # List of collection names used for caching
    COLLECTIONS = [
        "competitions",
        "clubs", 
        "players", 
        "player_market_values", 
        "player_transfers", 
        "player_jersey_numbers", 
        "player_stats", 
        "player_achievements", 
        "player_injuries"
    ]
    
    @staticmethod
    async def get_cached_response(collection_name: str, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a cached response from MongoDB.
        
        Args:
            collection_name: Name of the collection to search in
            resource_id: ID of the resource to fetch
            
        Returns:
            Cached response or None if not found
        """
        return await Database.find_one(collection_name, {"id": resource_id})
        
    @staticmethod
    async def get_all_cached_responses(collection_name: str, limit: int = 0, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Get all cached responses from a collection.
        
        Args:
            collection_name: Name of the collection to get items from
            limit: Maximum number of items to return (default: 0, no limit)
            skip: Number of items to skip (default: 0)
            
        Returns:
            List of cached items
        """
        return await Database.find_all(collection_name, {}, limit=limit, skip=skip)
    
    @staticmethod
    async def count_cached_responses(collection_name: str, query: Dict[str, Any] = None) -> int:
        """
        Count the number of documents in a collection.
        
        Args:
            collection_name: Name of the collection to count items in
            query: Optional query to filter which documents to count
            
        Returns:
            Number of documents in the collection
        """
        collection = await Database.get_collection(collection_name)
        return await collection.count_documents(query or {})
    
    @staticmethod
    async def is_cache_expired(data: Dict[str, Any]) -> bool:
        """
        Check if cached data is expired (older than CACHE_EXPIRATION_DAYS).
        
        Args:
            data: Cached data with updatedAt field
            
        Returns:
            True if cache is expired, False otherwise
        """
        if not data or "updatedAt" not in data:
            return True
            
        try:
            # Parse the updatedAt timestamp (could be string or datetime object)
            if isinstance(data["updatedAt"], str):
                updated_at = datetime.fromisoformat(data["updatedAt"].replace("Z", "+00:00"))
            else:
                updated_at = data["updatedAt"]
                
            # Check if the cache is older than CACHE_EXPIRATION_DAYS
            return datetime.utcnow() - updated_at > timedelta(days=CacheService.CACHE_EXPIRATION_DAYS)
        except (ValueError, TypeError):
            # If there's any error parsing the date, consider the cache expired
            return True
    
    @staticmethod
    async def cache_response(collection_name: str, data: Dict[str, Any]) -> str:
        """
        Cache a response in MongoDB.
        
        Args:
            collection_name: Name of the collection to store in
            data: Data to cache
            
        Returns:
            ID of the inserted document
        """
        # Add updatedAt timestamp
        data["updatedAt"] = datetime.utcnow()
        
        # Check if the record already exists
        existing = await Database.find_one(collection_name, {"id": data["id"]})
        
        if existing:
            # Update the existing document
            await Database.update_one(
                collection_name,
                {"id": data["id"]},
                {"$set": data}
            )
            return data["id"]
        else:
            # Set createdAt timestamp for new documents
            data["createdAt"] = datetime.utcnow()
            # Insert a new document
            return await Database.insert_one(collection_name, data)
    
    @staticmethod
    async def handle_request(
        collection_name: str, 
        resource_id: str, 
        fetch_function: callable,
        response_model: Type[BaseModel] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Handle an API request with caching.
        
        Args:
            collection_name: Name of the collection to store in
            resource_id: ID of the resource to fetch
            fetch_function: Function to call if cache miss
            response_model: Pydantic model for response validation
            **kwargs: Additional arguments to pass to fetch_function
            
        Returns:
            Response data, either from cache or freshly fetched
        """
        # Check if we have a cached response
        cached = await CacheService.get_cached_response(collection_name, resource_id)
        
        if cached:
            # Remove MongoDB's _id field before returning
            if "_id" in cached:
                cached.pop("_id")
            return cached
        
        # If not cached, fetch from the API
        response = fetch_function(**kwargs)
        
        # Ensure the response has an ID field
        if hasattr(response, "id") and response.id:
            # Cache the response (convert to dict if it's a Pydantic model)
            data = response.dict() if hasattr(response, "dict") else response
            
            # Add updatedAt timestamp
            if not hasattr(data, "updatedAt") or not data.get("updatedAt"):
                data["updatedAt"] = datetime.utcnow().isoformat()
                
            await CacheService.cache_response(collection_name, data)
        
        return response
