// MongoDB initialization script
// This script is run when the MongoDB container starts for the first time

// Switch to the application database
db = db.getSiblingDB('fastapi_enterprise');

// Create application user with read/write permissions
db.createUser({
  user: 'fastapi_user',
  pwd: 'fastapi_password',
  roles: [
    {
      role: 'readWrite',
      db: 'fastapi_enterprise',
    },
  ],
});

// Create collections with validation (optional)
db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['email', 'username', 'hashed_password', 'is_active'],
      properties: {
        email: {
          bsonType: 'string',
          pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+.[a-zA-Z]{2,}$',
          description: 'Must be a valid email address',
        },
        username: {
          bsonType: 'string',
          minLength: 3,
          maxLength: 50,
          description: 'Username must be between 3 and 50 characters',
        },
        hashed_password: {
          bsonType: 'string',
          description: 'Hashed password is required',
        },
        is_active: {
          bsonType: 'bool',
          description: 'Active status is required',
        },
        full_name: {
          bsonType: ['string', 'null'],
          maxLength: 100,
          description: 'Full name can be up to 100 characters',
        },
        is_superuser: {
          bsonType: 'bool',
          description: 'Superuser flag',
        },
        is_verified: {
          bsonType: 'bool',
          description: 'Email verification status',
        },
        created_at: {
          bsonType: 'date',
          description: 'Account creation timestamp',
        },
        updated_at: {
          bsonType: 'date',
          description: 'Last update timestamp',
        },
        last_login: {
          bsonType: ['date', 'null'],
          description: 'Last login timestamp',
        },
      },
    },
  },
});

// Create indexes for better query performance
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ username: 1 }, { unique: true });
db.users.createIndex({ created_at: 1 });
db.users.createIndex({ email: 1, is_active: 1 });

// Create user sessions collection
db.createCollection('user_sessions', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['user_id', 'refresh_token_hash', 'is_active', 'expires_at'],
      properties: {
        user_id: {
          bsonType: 'string',
          description: 'User ID is required',
        },
        refresh_token_hash: {
          bsonType: 'string',
          description: 'Refresh token hash is required',
        },
        is_active: {
          bsonType: 'bool',
          description: 'Active status is required',
        },
        expires_at: {
          bsonType: 'date',
          description: 'Expiration date is required',
        },
      },
    },
  },
});

// Create indexes for user sessions
db.user_sessions.createIndex({ user_id: 1 });
db.user_sessions.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 }); // TTL index
db.user_sessions.createIndex({ user_id: 1, is_active: 1 });

// Create test database
db = db.getSiblingDB('fastapi_enterprise_test');
db.createUser({
  user: 'fastapi_test_user',
  pwd: 'fastapi_test_password',
  roles: [
    {
      role: 'readWrite',
      db: 'fastapi_enterprise_test',
    },
  ],
});

print('MongoDB initialization completed successfully');
