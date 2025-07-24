# app/services/base_service.py

from typing import List, Optional, Dict, Any, TypeVar, Generic
from pymongo.database import Database
from pymongo.collection import Collection
from bson import ObjectId
import logging
from datetime import datetime
from app.schemas.common import PaginationParams, PaginatedResponse
from starlette.concurrency import run_in_threadpool

T = TypeVar('T')

class BaseService(Generic[T]):
    """
    Base service class providing common CRUD operations.
    Generic type T represents the Pydantic model for the entity.
    """
    
    def __init__(self, collection_name: str, db):
        """
        Initialize the base service.
        
        Args:
            collection_name: Name of the MongoDB collection
            db_uri: MongoDB connection string
            db_name: Database name
        """
        self.collection_name = collection_name
        self.db = db
        self.collection: Collection = self.db[collection_name]
        self.logger = logging.getLogger(f"{__name__}.{collection_name}")
        self.model = None  # Should be set in child class

    async def create(self, data: T) -> T:
        """
        Create a new entity.
        
        Args:
            data: Entity data
            
        Returns:
            T: Created entity
        """
        try:
            # Convert Pydantic model to dict
            data_dict = data.model_dump(mode='json', by_alias=True, exclude={'id'})
            data_dict['created_at'] = datetime.utcnow()
            
            # Insert into database
            result = await run_in_threadpool(self.collection.insert_one, data_dict)
            
            # Return created entity with ID
            created_doc = await self.get_by_id(result.inserted_id)
            return created_doc
            
        except Exception as e:
            self.logger.error(f"Error creating {self.collection_name}: {str(e)}")
            raise

    async def get_by_id(self, entity_id: Any) -> Optional[T]:
        """
        Get entity by ID.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Optional[T]: Entity or None
        """
        try:
            # Handle both string and ObjectId
            if isinstance(entity_id, str):
                try:
                    entity_id = ObjectId(entity_id)
                except:
                    pass
            
            doc = await run_in_threadpool(self.collection.find_one, {"_id": entity_id})
            if doc:
                return self.model(**doc)
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting {self.collection_name} by ID: {str(e)}")
            return None

    async def get_all(
        self, 
        pagination: PaginationParams,
        filters: Dict[str, Any],
        sort_by: str,
        sort_order: str
    ) -> PaginatedResponse[T]:
        """
        Get all entities with pagination and filtering.
        
        Args:
            pagination: Pagination parameters
            filters: Filter criteria
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            
        Returns:
            PaginatedResponse[T]: Paginated response
        """
        try:
            # Default pagination
            query = filters or {}
            
            # Build query
            total = await run_in_threadpool(self.collection.count_documents, query)
            
            # Calculate skip
            skip = (pagination.page - 1) * pagination.size
            
            # Get documents
            cursor = self.collection.find(query).skip(skip).limit(pagination.size)
            
            # Build sort
            if sort_by:
                from pymongo import ASCENDING, DESCENDING
                sort_direction = DESCENDING if sort_order.lower() == "desc" else ASCENDING
                cursor = cursor.sort(sort_by, sort_direction)
            
            # Convert to models
            items = [self.model(**doc) for doc in await run_in_threadpool(list, cursor)]
            
            # Calculate pagination info
            pages = (total + pagination.size - 1) // pagination.size
            has_next = pagination.page < pages
            has_prev = pagination.page > 1
            
            return PaginatedResponse(
                items=items,
                total=total,
                page=pagination.page,
                size=pagination.size,
                pages=pages,
                has_next=has_next,
                has_prev=has_prev
            )
            
        except Exception as e:
            self.logger.error(f"Error getting {self.collection_name}: {str(e)}")
            raise

    async def update(self, entity_id: str, data: T) -> Optional[T]:
        """
        Update an entity.
        
        Args:
            entity_id: Entity ID
            data: Updated entity data
            
        Returns:
            Optional[T]: Updated entity or None
        """
        try:
            # Handle both string and ObjectId
            if isinstance(entity_id, str):
                try:
                    entity_id = ObjectId(entity_id)
                except:
                    pass
            
            # Convert Pydantic model to dict, exclude ID
            update_dict = data.model_dump(mode='json', by_alias=True, exclude={'id'}, exclude_unset=True)
            update_dict['updated_at'] = datetime.utcnow()
            
            # Update in database
            result = await run_in_threadpool(self.collection.update_one,
                {"_id": entity_id},
                {"$set": update_dict}
            )
            
            if result.modified_count == 0:
                return None
            
            # Return updated entity
            return await self.get_by_id(str(entity_id))
            
        except Exception as e:
            self.logger.error(f"Error updating {self.collection_name}: {str(e)}")
            return None

    async def delete(self, entity_id: str) -> bool:
        """
        Delete an entity.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            # Handle both string and ObjectId
            if isinstance(entity_id, str):
                try:
                    entity_id = ObjectId(entity_id)
                except:
                    pass
            
            result = await run_in_threadpool(self.collection.delete_one, {"_id": entity_id})
            return result.deleted_count > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting {self.collection_name}: {str(e)}")
            return False

    async def bulk_create(self, data_list: List[T]) -> Dict[str, int]:
        """
        Create multiple entities in bulk.
        
        Args:
            data_list: List of entity data
            
        Returns:
            Dict[str, int]: Success and error counts
        """
        try:
            # Convert Pydantic models to dicts
            data_dicts = [item.model_dump(mode='json', by_alias=True, exclude={'id'}) for item in data_list]
            
            # Insert in bulk
            result = await run_in_threadpool(self.collection.insert_many, data_dicts)
            
            return {
                "success_count": len(result.inserted_ids),
                "error_count": 0
            }
            
        except Exception as e:
            self.logger.error(f"Error bulk creating {self.collection_name}: {str(e)}")
            return {
                "success_count": 0,
                "error_count": len(data_list)
            }

    async def search(
        self, 
        query: str, 
        fields: List[str] = None,
        pagination: PaginationParams = None
    ) -> PaginatedResponse[T]:
        """
        Search entities by text query.
        
        Args:
            query: Search query
            fields: Fields to search in
            pagination: Pagination parameters
            
        Returns:
            PaginatedResponse[T]: Search results
        """
        try:
            if not pagination:
                pagination = PaginationParams()
            
            # Build text search query
            search_query = {"$text": {"$search": query}}
            
            # Get total count
            total = await run_in_threadpool(self.collection.count_documents, search_query)
            
            # Calculate skip
            skip = (pagination.page - 1) * pagination.size
            
            # Get documents with text score
            cursor = self.collection.find(
                search_query,
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).skip(skip).limit(pagination.size)
            
            # Convert to models
            items = [self.model(**doc) for doc in await run_in_threadpool(list, cursor)]
            
            # Calculate pagination info
            pages = (total + pagination.size - 1) // pagination.size
            has_next = pagination.page < pages
            has_prev = pagination.page > 1
            
            return PaginatedResponse(
                items=items,
                total=total,
                page=pagination.page,
                size=pagination.size,
                pages=pages,
                has_next=has_next,
                has_prev=has_prev
            )
            
        except Exception as e:
            self.logger.error(f"Error searching {self.collection_name}: {str(e)}")
            raise

    async def count(self, filters: Dict[str, Any] = None) -> int:
        """
        Count entities with optional filters.
        
        Args:
            filters: Filter criteria
            
        Returns:
            int: Count of entities
        """
        try:
            query = filters or {}
            return await run_in_threadpool(self.collection.count_documents, query)
            
        except Exception as e:
            self.logger.error(f"Error counting {self.collection_name}: {str(e)}")
            return 0

    def close(self):
        """Close the database connection."""
        # No explicit close needed here as pymongo.Database handles connection pooling
        pass 