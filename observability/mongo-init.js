// MongoDB initialization script for pricing database
db = db.getSiblingDB('pricing');

// Create pricing user
db.createUser({
  user: 'pricing_user',
  pwd: 'pricing_password',
  roles: [
    {
      role: 'readWrite',
      db: 'pricing'
    }
  ]
});

// Create collections with initial indexes
db.createCollection('pricing_explanations');
db.createCollection('pricing_audit_log');
db.createCollection('pricing_metrics');

// Create indexes for pricing_explanations
db.pricing_explanations.createIndex({ "calculation_id": 1 }, { unique: true });
db.pricing_explanations.createIndex({ "timestamp": -1 });
db.pricing_explanations.createIndex({
  "part_specification.material": 1,
  "part_specification.process": 1
});
db.pricing_explanations.createIndex({ "part_specification.quantity": 1 });
db.pricing_explanations.createIndex({ "pricing_request_params.customer_tier": 1 });
db.pricing_explanations.createIndex({ "best_price_tier": 1 });
db.pricing_explanations.createIndex({ "limits_applied": 1 });

// Create indexes for pricing_audit_log
db.pricing_audit_log.createIndex({ "timestamp": -1 });
db.pricing_audit_log.createIndex({ "user_id": 1, "timestamp": -1 });
db.pricing_audit_log.createIndex({ "calculation_id": 1 });

// Create indexes for pricing_metrics
db.pricing_metrics.createIndex({ "date": -1 });
db.pricing_metrics.createIndex({ "metric_type": 1, "date": -1 });

// Insert sample data for testing
db.pricing_explanations.insertOne({
  "calculation_id": "sample-123",
  "timestamp": new Date().toISOString(),
  "part_specification": {
    "material": "aluminum",
    "process": "cnc",
    "quantity": 10
  },
  "pricing_request_params": {
    "customer_tier": "standard"
  },
  "best_price_tier": "standard",
  "limits_applied": false,
  "calculation_duration_ms": 150
});

print('Pricing database initialized successfully');
