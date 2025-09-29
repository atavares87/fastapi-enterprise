"""
Repository Pattern Implementation - Data Access Layer Abstractions

This module provides the foundation for the repository pattern implementation,
defining abstract interfaces and concrete implementations for different data stores.
Following hexagonal architecture principles, repositories isolate domain logic
from data persistence concerns.

Architecture Components:
- 🎨 Abstract Repository: Generic CRUD interface with type safety
- 💾 SQL Repository: PostgreSQL implementation with SQLAlchemy ORM
- 📄 MongoDB Repository: Document store implementation with Motor/Beanie
- ⚡ Redis Repository: Key-value caching with async Redis operations

Key Features:
- Generic type safety with TypeVar for domain models
- Async/await support for all database operations
- Consistent error handling across data store types
- Pagination support for large result sets
- Transaction support where applicable

Example Usage:
    # SQL Repository
    user_repo = SQLRepository[User](session, User)
    user = await user_repo.create(CreateUserSchema(name="John"))

    # MongoDB Repository
    doc_repo = MongoRepository[Document](database, "documents")
    docs = await doc_repo.list(skip=0, limit=10)

    # Redis Cache
    cache_repo = RedisRepository[CacheData](redis_client)
    await cache_repo.set("key", data, ttl=3600)
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from uuid import UUID

import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

# Generic types for repository pattern
T = TypeVar("T", bound=BaseModel)  # Domain model type
CreateSchema = TypeVar("CreateSchema", bound=BaseModel)  # Creation schema type
UpdateSchema = TypeVar("UpdateSchema", bound=BaseModel)  # Update schema type


class Repository(Generic[T], ABC):
    """
    Abstract base repository interface defining standard data access patterns.

    This generic interface establishes the contract for all repository implementations,
    ensuring consistent data access patterns across different storage backends.
    Uses Python generics to maintain type safety and provide excellent IDE support.

    Design Principles:
    - Interface Segregation: Clean, focused interface for CRUD operations
    - Dependency Inversion: Depend on abstractions, not concrete implementations
    - Generic Type Safety: Compile-time type checking for domain models
    - Async First: All operations support modern async/await patterns

    Standard Operations:
    - create(): Add new entities to the data store
    - get_by_id(): Retrieve entities by unique identifier
    - update(): Modify existing entities with validation
    - delete(): Remove entities from the data store
    - list(): Query entities with filtering and pagination
    - exists(): Check entity existence without full retrieval

    Error Handling:
    All implementations should raise RepositoryError for data access failures,
    providing consistent error handling across the application.
    """

    @abstractmethod
    async def create(self, data: CreateSchema) -> T:
        """
        Create a new entity.

        Args:
            data: Creation data for the entity

        Returns:
            Created entity

        Raises:
            RepositoryError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: int | str | UUID) -> T | None:
        """
        Get entity by ID.

        Args:
            entity_id: Unique identifier for the entity

        Returns:
            Entity if found, None otherwise

        Raises:
            RepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
    ) -> list[T]:
        """
        Get multiple entities with pagination and filtering.

        Args:
            skip: Number of entities to skip (pagination)
            limit: Maximum number of entities to return
            filters: Optional filters to apply

        Returns:
            List of entities matching criteria

        Raises:
            RepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
    async def update(
        self,
        entity_id: int | str | UUID,
        data: UpdateSchema,
    ) -> T | None:
        """
        Update an existing entity.

        Args:
            entity_id: Unique identifier for the entity
            data: Update data for the entity

        Returns:
            Updated entity if found, None otherwise

        Raises:
            RepositoryError: If update fails
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: int | str | UUID) -> bool:
        """
        Delete an entity by ID.

        Args:
            entity_id: Unique identifier for the entity

        Returns:
            True if entity was deleted, False if not found

        Raises:
            RepositoryError: If deletion fails
        """
        pass

    @abstractmethod
    async def exists(self, entity_id: int | str | UUID) -> bool:
        """
        Check if an entity exists by ID.

        Args:
            entity_id: Unique identifier for the entity

        Returns:
            True if entity exists, False otherwise

        Raises:
            RepositoryError: If check fails
        """
        pass

    @abstractmethod
    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """
        Count entities matching optional filters.

        Args:
            filters: Optional filters to apply

        Returns:
            Number of entities matching criteria

        Raises:
            RepositoryError: If count fails
        """
        pass


class PostgresRepository(Repository[T], Generic[T], ABC):
    """
    Base PostgreSQL repository implementation.

    This class provides common functionality for PostgreSQL-based repositories
    using SQLAlchemy. Concrete repositories should inherit from this class
    and implement the abstract methods.
    """

    def __init__(self, session: AsyncSession, model: type[Any]):
        """
        Initialize PostgreSQL repository.

        Args:
            session: SQLAlchemy async session
            model: SQLAlchemy model class
        """
        self.session = session
        self.model = model

    async def exists(self, entity_id: int | str | UUID) -> bool:
        """Check if entity exists in PostgreSQL."""
        from sqlalchemy import exists as sql_exists
        from sqlalchemy import select

        query = select(sql_exists().where(self.model.id == entity_id))
        result = await self.session.execute(query)
        return result.scalar() or False

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count entities in PostgreSQL."""
        from sqlalchemy import func, select

        query = select(func.count(self.model.id))

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        result = await self.session.execute(query)
        return result.scalar() or 0


class MongoRepository(Repository[T], Generic[T], ABC):
    """
    Base MongoDB repository implementation.

    This class provides common functionality for MongoDB-based repositories
    using Motor. Concrete repositories should inherit from this class
    and implement the abstract methods.
    """

    def __init__(self, database: AsyncIOMotorDatabase[Any], collection_name: str):
        """
        Initialize MongoDB repository.

        Args:
            database: MongoDB database instance
            collection_name: Name of the collection
        """
        self.database = database
        self.collection = database[collection_name]
        self.collection_name = collection_name

    async def exists(self, entity_id: int | str | UUID) -> bool:
        """Check if entity exists in MongoDB."""
        count = await self.collection.count_documents({"_id": entity_id})
        return count > 0

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count entities in MongoDB."""
        filter_dict = filters or {}
        return await self.collection.count_documents(filter_dict)


class CacheRepository(ABC):
    """
    Base cache repository interface.

    This interface defines operations for caching frequently accessed data
    using Redis or other caching backends.
    """

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """
        Get cached value by key.

        Args:
            key: Cache key

        Returns:
            Cached value if exists, None otherwise
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: str,
        expire_seconds: int | None = None,
    ) -> None:
        """
        Set cached value with optional expiration.

        Args:
            key: Cache key
            value: Value to cache
            expire_seconds: Expiration time in seconds (optional)
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete cached value by key.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if key didn't exist
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if cached value exists.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        pass


class RedisRepository(CacheRepository):
    """
    Redis implementation of cache repository.

    This class provides caching functionality using Redis as the backend.
    """

    def __init__(self, redis_client: redis.Redis):
        """
        Initialize Redis repository.

        Args:
            redis_client: Redis async client
        """
        self.redis = redis_client

    async def get(self, key: str) -> str | None:
        """Get value from Redis cache."""
        value = await self.redis.get(key)
        return value.decode("utf-8") if value else None

    async def set(
        self,
        key: str,
        value: str,
        expire_seconds: int | None = None,
    ) -> None:
        """Set value in Redis cache with optional expiration."""
        if expire_seconds:
            await self.redis.setex(key, expire_seconds, value)
        else:
            await self.redis.set(key, value)

    async def delete(self, key: str) -> bool:
        """Delete value from Redis cache."""
        result = await self.redis.delete(key)
        return bool(result)

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        result = await self.redis.exists(key)
        return bool(result)


class RepositoryError(Exception):
    """
    Base exception for repository operations.

    This exception should be raised when repository operations fail
    due to database errors, validation errors, or other issues.
    """

    def __init__(self, message: str, operation: str, entity_type: str):
        """
        Initialize repository error.

        Args:
            message: Error message
            operation: Operation that failed (create, update, delete, etc.)
            entity_type: Type of entity involved in the operation
        """
        self.operation = operation
        self.entity_type = entity_type
        super().__init__(message)


class EntityNotFoundError(RepositoryError):
    """Exception raised when an entity is not found."""

    def __init__(self, entity_type: str, entity_id: int | str | UUID):
        """
        Initialize entity not found error.

        Args:
            entity_type: Type of entity that was not found
            entity_id: ID of the entity that was not found
        """
        message = f"{entity_type} with id {entity_id} not found"
        super().__init__(message, "get", entity_type)


class EntityAlreadyExistsError(RepositoryError):
    """Exception raised when trying to create an entity that already exists."""

    def __init__(self, entity_type: str, identifier: str):
        """
        Initialize entity already exists error.

        Args:
            entity_type: Type of entity that already exists
            identifier: Identifier that conflicts (e.g., email, username)
        """
        message = f"{entity_type} with {identifier} already exists"
        super().__init__(message, "create", entity_type)


class RepositoryConnectionError(RepositoryError):
    """Exception raised when there are database connection issues."""

    def __init__(self, entity_type: str, operation: str, original_error: str):
        """
        Initialize repository connection error.

        Args:
            entity_type: Type of entity involved in the operation
            operation: Operation that failed
            original_error: Original error message from database
        """
        message = f"Database connection error during {operation}: {original_error}"
        super().__init__(message, operation, entity_type)
