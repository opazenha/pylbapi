from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

# Get MongoDB URI from environment variables or use a default for local development
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/transfermarkt")

class Database:
    client: AsyncIOMotorClient = None

    @classmethod
    async def connect_to_mongodb(cls):
        """Connect to MongoDB."""
        cls.client = AsyncIOMotorClient(MONGODB_URI)
        print("Connected to MongoDB")

    @classmethod
    async def close_mongodb_connection(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            print("Closed MongoDB connection")

    @classmethod
    def get_db(cls):
        """Return database instance."""
        return cls.client.get_database()

    @classmethod
    async def get_collection(cls, collection_name: str):
        """Get collection from the database."""
        return cls.get_db()[collection_name]

    @classmethod
    async def find_one(cls, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document in the collection."""
        collection = await cls.get_collection(collection_name)
        return await collection.find_one(query)
        
    @classmethod
    async def find_all(cls, collection_name: str, query: Dict[str, Any] = None, limit: int = 0, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Find all documents in the collection that match the query.
        
        Args:
            collection_name: Name of the collection to search in
            query: Query to filter documents (default: None, returns all documents)
            limit: Maximum number of documents to return (default: 0, no limit)
            skip: Number of documents to skip (default: 0)
            
        Returns:
            List of documents
        """
        collection = await cls.get_collection(collection_name)
        query = query or {}
        # Exclude the MongoDB internal _id field as it's not JSON serializable by default
        cursor = collection.find(query, {'_id': 0}).skip(skip)
        
        if limit > 0:
            cursor = cursor.limit(limit)
            
        # If limit is 0, fetch all (or a reasonably large number to prevent excessive memory usage)
        # Otherwise, fetch only the specified number of documents.
        # Since the API enforces a limit (default 10, max 50), directly using limit is safe here.
        return await cursor.to_list(length=limit if limit > 0 else None)

    @classmethod
    async def insert_one(cls, collection_name: str, document: Dict[str, Any]) -> str:
        """Insert a document into the collection."""
        collection = await cls.get_collection(collection_name)
        # Add timestamp for when the document was created
        document["createdAt"] = datetime.utcnow()
        result = await collection.insert_one(document)
        return str(result.inserted_id)

    @classmethod
    async def update_one(cls, collection_name: str, query: Dict[str, Any], update: Dict[str, Any]) -> bool:
        """Update a document in the collection."""
        collection = await cls.get_collection(collection_name)
        # Update the updatedAt timestamp
        update_with_timestamp = {"$set": {**update.get("$set", {}), "updatedAt": datetime.utcnow()}}
        result = await collection.update_one(query, update_with_timestamp)
        return result.modified_count > 0

    @classmethod
    async def find_or_create(cls, collection_name: str, query: Dict[str, Any], document: Dict[str, Any]) -> Dict[str, Any]:
        """Find a document or create it if it doesn't exist."""
        existing = await cls.find_one(collection_name, query)
        if existing:
            return existing
        
        await cls.insert_one(collection_name, document)
        return await cls.find_one(collection_name, query)
        
    @classmethod
    async def get_collection_names(cls) -> List[str]:
        """Get a list of all collection names in the database."""
        db = cls.get_db()
        return await db.list_collection_names()
