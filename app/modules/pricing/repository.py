"""
Pricing Repository for MongoDB Storage

Handles persistence of pricing calculations, explanations, and audit trails
for business intelligence and compliance purposes.
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError

from app.modules.pricing.explainability import PricingExplanation


class PricingRepository:
    """Repository for pricing data persistence and retrieval."""

    def __init__(self, database: AsyncIOMotorDatabase[dict[str, Any]]):
        """
        Initialize repository with MongoDB database.

        Args:
            database: MongoDB database instance
        """
        self.database = database
        self.pricing_explanations: AsyncIOMotorCollection[dict[str, Any]] = (
            database.pricing_explanations
        )
        self.pricing_audit_log: AsyncIOMotorCollection[dict[str, Any]] = (
            database.pricing_audit_log
        )
        self.pricing_metrics: AsyncIOMotorCollection[dict[str, Any]] = (
            database.pricing_metrics
        )

    async def initialize_indexes(self) -> None:
        """Create database indexes for optimal query performance."""

        # Pricing explanations indexes
        await self.pricing_explanations.create_index(
            [("calculation_id", ASCENDING)], unique=True
        )

        await self.pricing_explanations.create_index([("timestamp", DESCENDING)])

        await self.pricing_explanations.create_index(
            [
                ("part_specification.material", ASCENDING),
                ("part_specification.process", ASCENDING),
            ]
        )

        await self.pricing_explanations.create_index(
            [("part_specification.quantity", ASCENDING)]
        )

        await self.pricing_explanations.create_index(
            [("pricing_request_params.customer_tier", ASCENDING)]
        )

        await self.pricing_explanations.create_index([("best_price_tier", ASCENDING)])

        await self.pricing_explanations.create_index([("limits_applied", ASCENDING)])

        # Audit log indexes
        await self.pricing_audit_log.create_index([("timestamp", DESCENDING)])

        await self.pricing_audit_log.create_index(
            [("user_id", ASCENDING), ("timestamp", DESCENDING)]
        )

        await self.pricing_audit_log.create_index([("calculation_id", ASCENDING)])

        # Metrics indexes
        await self.pricing_metrics.create_index([("date", DESCENDING)])

        await self.pricing_metrics.create_index(
            [("metric_type", ASCENDING), ("date", DESCENDING)]
        )

    async def save_pricing_explanation(self, explanation: PricingExplanation) -> bool:
        """
        Save a complete pricing explanation to MongoDB.

        Args:
            explanation: Complete pricing explanation

        Returns:
            True if saved successfully, False if already exists

        Raises:
            Exception: If save operation fails
        """
        try:
            document = explanation.to_dict()
            await self.pricing_explanations.insert_one(document)
            return True
        except DuplicateKeyError:
            # Calculation already exists
            return False
        except Exception as e:
            raise Exception(f"Failed to save pricing explanation: {str(e)}") from e

    async def get_pricing_explanation(
        self, calculation_id: UUID
    ) -> dict[str, Any] | None:
        """
        Retrieve a pricing explanation by calculation ID.

        Args:
            calculation_id: Unique calculation identifier

        Returns:
            Pricing explanation document or None if not found
        """
        return await self.pricing_explanations.find_one(
            {"calculation_id": str(calculation_id)}
        )

    async def search_pricing_explanations(
        self,
        material: str | None = None,
        process: str | None = None,
        customer_tier: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 100,
        skip: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Search pricing explanations with filters.

        Args:
            material: Filter by material type
            process: Filter by manufacturing process
            customer_tier: Filter by customer tier
            date_from: Start date filter
            date_to: End date filter
            limit: Maximum number of results
            skip: Number of results to skip

        Returns:
            List of matching pricing explanation documents
        """
        filter_query: dict[str, Any] = {}

        if material:
            filter_query["part_specification.material"] = material

        if process:
            filter_query["part_specification.process"] = process

        if customer_tier:
            filter_query["pricing_request_params.customer_tier"] = customer_tier

        if date_from or date_to:
            date_filter = {}
            if date_from:
                date_filter["$gte"] = date_from.isoformat()
            if date_to:
                date_filter["$lte"] = date_to.isoformat()
            filter_query["timestamp"] = date_filter

        cursor = self.pricing_explanations.find(filter_query).sort(
            "timestamp", DESCENDING
        )
        cursor = cursor.skip(skip).limit(limit)

        return await cursor.to_list(length=limit)

    async def get_pricing_analytics(
        self, date_from: datetime, date_to: datetime
    ) -> dict[str, Any]:
        """
        Get pricing analytics for a date range.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            Dictionary containing analytics data
        """
        pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "timestamp": {
                        "$gte": date_from.isoformat(),
                        "$lte": date_to.isoformat(),
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_calculations": {"$sum": 1},
                    "calculations_with_limits": {
                        "$sum": {"$cond": ["$limits_applied", 1, 0]}
                    },
                    "avg_calculation_duration": {"$avg": "$calculation_duration_ms"},
                    "material_breakdown": {"$push": "$part_specification.material"},
                    "process_breakdown": {"$push": "$part_specification.process"},
                    "tier_selections": {"$push": "$best_price_tier"},
                    "avg_quantities": {"$avg": "$part_specification.quantity"},
                }
            },
        ]

        result = await self.pricing_explanations.aggregate(pipeline).to_list(length=1)

        if not result:
            return {
                "total_calculations": 0,
                "calculations_with_limits": 0,
                "avg_calculation_duration": 0,
                "material_breakdown": {},
                "process_breakdown": {},
                "tier_selections": {},
                "avg_quantities": 0,
            }

        analytics: dict[str, Any] = result[0]

        # Count occurrences for breakdowns
        from collections import Counter

        analytics["material_breakdown"] = dict(Counter(analytics["material_breakdown"]))
        analytics["process_breakdown"] = dict(Counter(analytics["process_breakdown"]))
        analytics["tier_selections"] = dict(Counter(analytics["tier_selections"]))

        return analytics

    async def log_pricing_audit_event(
        self,
        calculation_id: UUID,
        user_id: str | None,
        action: str,
        details: dict[str, Any],
        ip_address: str | None = None,
    ) -> None:
        """
        Log a pricing audit event.

        Args:
            calculation_id: Related calculation ID
            user_id: User who performed the action
            action: Action description
            details: Additional event details
            ip_address: User's IP address
        """
        audit_event = {
            "calculation_id": str(calculation_id),
            "user_id": user_id,
            "action": action,
            "details": details,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.pricing_audit_log.insert_one(audit_event)

    async def get_audit_trail(
        self,
        calculation_id: UUID | None = None,
        user_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Retrieve audit trail with filters.

        Args:
            calculation_id: Filter by calculation ID
            user_id: Filter by user ID
            date_from: Start date filter
            date_to: End date filter
            limit: Maximum number of results

        Returns:
            List of audit events
        """
        filter_query: dict[str, Any] = {}

        if calculation_id:
            filter_query["calculation_id"] = str(calculation_id)

        if user_id:
            filter_query["user_id"] = user_id

        if date_from or date_to:
            date_filter = {}
            if date_from:
                date_filter["$gte"] = date_from.isoformat()
            if date_to:
                date_filter["$lte"] = date_to.isoformat()
            filter_query["timestamp"] = date_filter

        cursor = self.pricing_audit_log.find(filter_query).sort("timestamp", DESCENDING)
        cursor = cursor.limit(limit)

        return await cursor.to_list(length=limit)

    async def save_daily_metrics(self, date: datetime, metrics: dict[str, Any]) -> None:
        """
        Save daily aggregated metrics.

        Args:
            date: Date for the metrics
            metrics: Metrics data
        """
        document = {
            "date": date.date().isoformat(),
            "metric_type": "daily_summary",
            "metrics": metrics,
            "generated_at": datetime.utcnow().isoformat(),
        }

        await self.pricing_metrics.replace_one(
            {"date": date.date().isoformat(), "metric_type": "daily_summary"},
            document,
            upsert=True,
        )

    async def get_metrics_by_date_range(
        self, date_from: datetime, date_to: datetime, metric_type: str = "daily_summary"
    ) -> list[dict[str, Any]]:
        """
        Get metrics for a date range.

        Args:
            date_from: Start date
            date_to: End date
            metric_type: Type of metrics to retrieve

        Returns:
            List of metrics documents
        """
        filter_query = {
            "metric_type": metric_type,
            "date": {
                "$gte": date_from.date().isoformat(),
                "$lte": date_to.date().isoformat(),
            },
        }

        cursor = self.pricing_metrics.find(filter_query).sort("date", ASCENDING)
        return await cursor.to_list(length=None)

    async def cleanup_old_data(self, retention_days: int = 365) -> dict[str, int | str]:
        """
        Clean up old data beyond retention period.

        Args:
            retention_days: Number of days to retain data

        Returns:
            Dictionary with cleanup statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        cutoff_iso = cutoff_date.isoformat()

        # Clean up old explanations
        explanations_result = await self.pricing_explanations.delete_many(
            {"timestamp": {"$lt": cutoff_iso}}
        )

        # Clean up old audit logs
        audit_result = await self.pricing_audit_log.delete_many(
            {"timestamp": {"$lt": cutoff_iso}}
        )

        # Clean up old metrics (keep longer retention for metrics)
        metrics_cutoff = datetime.utcnow() - timedelta(days=retention_days * 2)
        metrics_result = await self.pricing_metrics.delete_many(
            {"generated_at": {"$lt": metrics_cutoff.isoformat()}}
        )

        return {
            "explanations_deleted": explanations_result.deleted_count,
            "audit_logs_deleted": audit_result.deleted_count,
            "metrics_deleted": metrics_result.deleted_count,
            "cutoff_date": cutoff_iso,
        }

    async def get_popular_configurations(
        self, date_from: datetime, date_to: datetime, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get most popular part configurations for a date range.

        Args:
            date_from: Start date
            date_to: End date
            limit: Maximum number of results

        Returns:
            List of popular configurations with counts
        """
        pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "timestamp": {
                        "$gte": date_from.isoformat(),
                        "$lte": date_to.isoformat(),
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "material": "$part_specification.material",
                        "process": "$part_specification.process",
                        "complexity_range": {
                            "$switch": {
                                "branches": [
                                    {
                                        "case": {
                                            "$lt": [
                                                "$part_specification.geometric_complexity_score",
                                                2.0,
                                            ]
                                        },
                                        "then": "Low (1.0-2.0)",
                                    },
                                    {
                                        "case": {
                                            "$lt": [
                                                "$part_specification.geometric_complexity_score",
                                                3.5,
                                            ]
                                        },
                                        "then": "Medium (2.0-3.5)",
                                    },
                                    {
                                        "case": {
                                            "$lt": [
                                                "$part_specification.geometric_complexity_score",
                                                4.5,
                                            ]
                                        },
                                        "then": "High (3.5-4.5)",
                                    },
                                ],
                                "default": "Very High (4.5-5.0)",
                            }
                        },
                    },
                    "count": {"$sum": 1},
                    "avg_quantity": {"$avg": "$part_specification.quantity"},
                    "avg_complexity": {
                        "$avg": "$part_specification.geometric_complexity_score"
                    },
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]

        return await self.pricing_explanations.aggregate(pipeline).to_list(length=limit)
