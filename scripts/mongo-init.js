// =============================================================================
// BLOOCUBE AI SERVICES - MONGODB INITIALIZATION SCRIPT
// =============================================================================

// Switch to the bloocube database
db = db.getSiblingDB('bloocube');

// Create collections with validation schemas
db.createCollection('ai_results', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['user_id', 'result_type', 'status'],
      properties: {
        user_id: {
          bsonType: 'objectId',
          description: 'User ID is required'
        },
        campaign_id: {
          bsonType: ['objectId', 'null'],
          description: 'Campaign ID (optional)'
        },
        result_type: {
          bsonType: 'string',
          enum: ['suggestion', 'analysis', 'matchmaking', 'competitor_analysis', 'content_optimization', 'trend_analysis'],
          description: 'Result type is required'
        },
        status: {
          bsonType: 'string',
          enum: ['processing', 'completed', 'failed', 'expired'],
          description: 'Status is required'
        },
        generated_at: {
          bsonType: 'date',
          description: 'Generation timestamp'
        },
        expires_at: {
          bsonType: 'date',
          description: 'Expiration timestamp'
        }
      }
    }
  }
});

db.createCollection('embeddings', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['content_id', 'embedding', 'content_type'],
      properties: {
        content_id: {
          bsonType: 'string',
          description: 'Content ID is required'
        },
        embedding: {
          bsonType: 'array',
          description: 'Embedding vector is required'
        },
        content_type: {
          bsonType: 'string',
          enum: ['post', 'campaign', 'user_profile', 'competitor_data'],
          description: 'Content type is required'
        },
        metadata: {
          bsonType: 'object',
          description: 'Additional metadata'
        }
      }
    }
  }
});

db.createCollection('competitor_data', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['username', 'platform', 'last_updated'],
      properties: {
        username: {
          bsonType: 'string',
          description: 'Username is required'
        },
        platform: {
          bsonType: 'string',
          enum: ['instagram', 'twitter', 'youtube', 'linkedin', 'facebook', 'tiktok'],
          description: 'Platform is required'
        },
        last_updated: {
          bsonType: 'date',
          description: 'Last update timestamp is required'
        }
      }
    }
  }
});

// Create indexes for better performance
print('Creating indexes...');

// AI Results indexes
db.ai_results.createIndex({ user_id: 1, result_type: 1 });
db.ai_results.createIndex({ campaign_id: 1 });
db.ai_results.createIndex({ status: 1 });
db.ai_results.createIndex({ generated_at: -1 });
db.ai_results.createIndex({ expires_at: 1 });
db.ai_results.createIndex({ 'content.numerical_score': -1 });

// Embeddings indexes
db.embeddings.createIndex({ content_id: 1 }, { unique: true });
db.embeddings.createIndex({ content_type: 1 });
db.embeddings.createIndex({ 'metadata.platform': 1 });
db.embeddings.createIndex({ created_at: -1 });

// Competitor data indexes
db.competitor_data.createIndex({ username: 1, platform: 1 }, { unique: true });
db.competitor_data.createIndex({ platform: 1 });
db.competitor_data.createIndex({ last_updated: -1 });
db.competitor_data.createIndex({ 'profile.followers': -1 });

// Create user for AI service
db.createUser({
  user: 'aiservice',
  pwd: 'aiservice123',
  roles: [
    {
      role: 'readWrite',
      db: 'bloocube'
    }
  ]
});

print('MongoDB initialization completed successfully!');
print('Created collections: ai_results, embeddings, competitor_data');
print('Created indexes for optimal performance');
print('Created user: aiservice');
