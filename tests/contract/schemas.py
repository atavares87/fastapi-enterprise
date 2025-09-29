"""
JSON Schema definitions for API contract validation.

These schemas define the expected structure and validation rules for
API requests and responses, serving as the contract specification.
"""

# Health check response schemas
HEALTH_BASIC_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["healthy", "unhealthy"]},
        "timestamp": {"type": "number"},
        "app_name": {"type": "string"},
        "version": {"type": "string"},
        "environment": {
            "type": "string",
            "enum": ["development", "production", "testing"],
        },
    },
    "required": ["status", "timestamp", "app_name", "version", "environment"],
    "additionalProperties": False,
}

HEALTH_DETAILED_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["healthy", "unhealthy"]},
        "timestamp": {"type": "number"},
        "app_name": {"type": "string"},
        "version": {"type": "string"},
        "environment": {
            "type": "string",
            "enum": ["development", "production", "testing"],
        },
        "services": {
            "type": "object",
            "properties": {
                "postgres": {"type": "boolean"},
                "mongodb": {"type": "boolean"},
                "redis": {"type": "boolean"},
            },
            "required": ["postgres", "mongodb", "redis"],
            "additionalProperties": False,
        },
        "checks": {
            "type": "object",
            "properties": {
                "application": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["healthy", "unhealthy"]}
                    },
                    "required": ["status"],
                },
                "postgres": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["healthy", "unhealthy"]}
                    },
                    "required": ["status"],
                },
                "mongodb": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["healthy", "unhealthy"]}
                    },
                    "required": ["status"],
                },
                "redis": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["healthy", "unhealthy"]}
                    },
                    "required": ["status"],
                },
            },
            "required": ["application", "postgres", "mongodb", "redis"],
            "additionalProperties": False,
        },
    },
    "required": [
        "status",
        "timestamp",
        "app_name",
        "version",
        "environment",
        "services",
        "checks",
    ],
    "additionalProperties": False,
}

ROOT_ENDPOINT_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "message": {"type": "string"},
        "version": {"type": "string"},
        "environment": {
            "type": "string",
            "enum": ["development", "production", "testing"],
        },
        "docs_url": {"type": "string"},
        "redoc_url": {"type": "string"},
        "health_check": {"type": "string"},
    },
    "required": [
        "message",
        "version",
        "environment",
        "docs_url",
        "redoc_url",
        "health_check",
    ],
    "additionalProperties": False,
}

# Pricing API schemas
PRICING_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "material": {"type": "string"},
        "quantity": {"type": "integer", "minimum": 1},
        "dimensions": {
            "type": "object",
            "properties": {
                "length_mm": {"type": "number", "minimum": 0},
                "width_mm": {"type": "number", "minimum": 0},
                "height_mm": {"type": "number", "minimum": 0},
            },
            "required": ["length_mm", "width_mm", "height_mm"],
            "additionalProperties": False,
        },
        "geometric_complexity_score": {
            "type": "number",
            "minimum": 1.0,
            "maximum": 5.0,
        },
        "process": {"type": "string"},
        "surface_finish": {"type": "string"},
        "tolerance_class": {"type": "string"},
        "special_requirements": {"type": "array", "items": {"type": "string"}},
        "delivery_timeline": {"type": "string"},
        "rush_order": {"type": "boolean"},
        "customer_tier": {"type": "string"},
    },
    "required": [
        "material",
        "quantity",
        "dimensions",
        "geometric_complexity_score",
        "process",
    ],
    "additionalProperties": False,
}

PRICING_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "part_specification": {
            "type": "object",
            "properties": {
                "dimensions": {
                    "type": "object",
                    "properties": {
                        "length_mm": {"type": "number"},
                        "width_mm": {"type": "number"},
                        "height_mm": {"type": "number"},
                        "volume_cm3": {"type": "number"},
                    },
                    "required": ["length_mm", "width_mm", "height_mm", "volume_cm3"],
                },
                "geometric_complexity_score": {"type": "number"},
                "material": {"type": "string"},
                "process": {"type": "string"},
            },
            "required": [
                "dimensions",
                "geometric_complexity_score",
                "material",
                "process",
            ],
        },
        "cost_breakdown": {
            "type": "object",
            "properties": {
                "material_cost": {"type": "number"},
                "labor_cost": {"type": "number"},
                "setup_cost": {"type": "number"},
                "complexity_adjustment": {"type": "number"},
                "overhead_cost": {"type": "number"},
                "total_cost": {"type": "number"},
            },
            "required": [
                "material_cost",
                "labor_cost",
                "setup_cost",
                "complexity_adjustment",
                "overhead_cost",
                "total_cost",
            ],
        },
        "pricing_tiers": {
            "type": "object",
            "properties": {
                "expedited": {"$ref": "#/$defs/pricing_tier"},
                "standard": {"$ref": "#/$defs/pricing_tier"},
                "economy": {"$ref": "#/$defs/pricing_tier"},
                "domestic_economy": {"$ref": "#/$defs/pricing_tier"},
            },
            "required": ["expedited", "standard", "economy", "domestic_economy"],
        },
        "estimated_weight_kg": {"type": "number"},
        "quantity": {"type": "integer"},
    },
    "required": [
        "part_specification",
        "cost_breakdown",
        "pricing_tiers",
        "estimated_weight_kg",
        "quantity",
    ],
    "$defs": {
        "pricing_tier": {
            "type": "object",
            "properties": {
                "base_cost": {"type": "number"},
                "margin": {"type": "number"},
                "shipping_cost": {"type": "number"},
                "volume_discount": {"type": "number"},
                "complexity_surcharge": {"type": "number"},
                "subtotal": {"type": "number"},
                "final_discount": {"type": "number"},
                "final_price": {"type": "number"},
                "price_per_unit": {"type": "number"},
            },
            "required": ["final_price", "price_per_unit"],
        }
    },
}

VALIDATION_ERROR_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "message": {"type": "string"},
                "details": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "loc": {"type": "array", "items": {"type": "string"}},
                            "msg": {"type": "string"},
                            "input": {},
                        },
                        "required": ["type", "loc", "msg"],
                    },
                },
            },
            "required": ["type", "message", "details"],
        }
    },
    "required": ["error"],
}

# Metadata endpoint schemas
MATERIALS_LIST_SCHEMA = {"type": "array", "items": {"type": "string"}, "minItems": 1}

PROCESSES_LIST_SCHEMA = {"type": "array", "items": {"type": "string"}, "minItems": 1}

TIERS_LIST_SCHEMA = {"type": "array", "items": {"type": "string"}, "minItems": 1}
