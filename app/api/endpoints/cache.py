from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Query, Response, Path
from pydantic import BaseModel
import logging
from json import JSONDecodeError

from app.db.cache_service import CacheService

router = APIRouter()
logger = logging.getLogger(__name__)


class CacheStats(BaseModel):
    """Statistics about cached collections."""
    collection_name: str
    count: int


@router.get(
    "/stats",
    response_model=List[CacheStats],
    summary="Get Cache Collection Statistics",
    description="Retrieves statistics for each cached collection, showing the collection name and the number of items currently cached in MongoDB.",
    response_description="A list containing statistics (name and item count) for each collection.",
    tags=["cache"]
)
async def get_cache_stats():
    """Get statistics about all cached collections."""
    stats = []
    try:
        for collection_name in CacheService.COLLECTIONS:
            # Use a more efficient method to count documents only
            count = await CacheService.count_cached_responses(collection_name)
            stats.append(CacheStats(collection_name=collection_name, count=count))
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving cache statistics: {str(e)}")


@router.get(
    "/{collection_name}",
    response_model=List[Dict[str, Any]], # Note: Returning generic dict as structure varies by collection
    summary="Get Cached Items from a Collection",
    description=(
        "Retrieves a paginated list of cached items from the specified MongoDB collection. "
        f"Valid collection names are: {', '.join(CacheService.COLLECTIONS)}. "
        "Use the 'limit' and 'skip' query parameters for pagination."
    ),
    response_description="A list containing the cached items (as dictionaries) from the specified collection.",
    tags=["cache"]
)
async def get_all_from_collection(
    collection_name: str = Path(..., description=f"Name of the collection to retrieve items from. Valid names: {', '.join(CacheService.COLLECTIONS)}"),
    limit: Optional[int] = Query(None, description="Maximum number of items to return. Omit for no limit (returns all items).", gt=0),
    skip: Optional[int] = Query(None, description="Number of items to skip. Omit for no skip.", ge=0),
    response: Response = None
):
    """
    Get all cached items from a collection.
    
    Args:
        collection_name: Name of the collection to get items from
        limit: Maximum number of items to return (default: 10, max: 50)
        skip: Number of items to skip (default: 0)
        
    Returns:
        List of cached items from the collection
    """
    try:
        if collection_name not in CacheService.COLLECTIONS:
            valid_collections = ", ".join(CacheService.COLLECTIONS)
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found. Valid collections: {valid_collections}"
            )
        
        # Determine effective limit and skip for the database query
        # Use 0 for 'no limit' / 'no skip' if user provided None, which database layer understands
        db_limit = limit or 0
        db_skip = skip or 0
        
        # Fetch results using the determined limit and skip
        results = await CacheService.get_all_cached_responses(collection_name, limit=db_limit, skip=db_skip)
        
        # Add pagination headers only if limit was provided by the user
        if limit is not None and response:
            total_count = await CacheService.count_cached_responses(collection_name)
            response.headers["X-Total-Count"] = str(total_count)
            response.headers["X-Page-Skip"] = str(db_skip) # Use the effective skip (could be 0)
            response.headers["X-Page-Limit"] = str(limit) # Use the user-provided limit
            response.headers["Access-Control-Expose-Headers"] = "X-Total-Count, X-Page-Skip, X-Page-Limit"
        
        return results
    except HTTPException as e:
        # Pass through HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"Error retrieving cached items from {collection_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving cached items: {str(e)}")
