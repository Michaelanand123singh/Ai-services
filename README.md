# Bloocube AI Services

A comprehensive AI-powered service for social media management, competitor analysis, and content optimization. Built with FastAPI, LangChain, and advanced ML models.

## 🚀 Features

### Core AI Capabilities
- **Competitor Analysis**: Deep analysis of competitor profiles across social platforms
- **Content Suggestions**: AI-powered hashtag, caption, and posting time recommendations
- **Brand-Creator Matching**: Intelligent matchmaking between brands and content creators
- **Performance Forecasting**: Predictive analytics for content performance
- **RAG Pipeline**: Retrieval-Augmented Generation for context-aware responses

### Social Media Integration
- **Multi-Platform Support**: Instagram, YouTube, Twitter, LinkedIn, Facebook
- **Data Collection**: Profile analysis, post metrics, engagement tracking
- **API Abstraction**: Unified interface for different social platforms

### Advanced Features
- **Vector Search**: Semantic similarity using embeddings
- **Structured Logging**: JSON-formatted logs with context
- **Error Handling**: Comprehensive exception handling
- **Input Validation**: Robust validation for all API inputs
- **Caching Support**: Redis integration for performance optimization
- **Background Tasks**: Async processing for long-running operations

## 📋 Prerequisites

- Python 3.11+
- MongoDB 4.4+
- Redis 6.0+
- OpenAI API Key
- Social Media API Keys (optional)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd AI-services
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy the example environment file
cp env.example .env

# Edit the .env file with your configuration
nano .env
```

### 5. Required Environment Variables
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# JWT Configuration
JWT_SECRET=your_jwt_secret_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Database Configuration
MONGODB_URL=mongodb://localhost:27017/bloocube_ai
REDIS_URL=redis://localhost:6379/0

# Vector Database Configuration
VECTOR_DB_TYPE=faiss
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here

# Social Media API Keys (Optional)
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here
YOUTUBE_API_KEY=your_youtube_api_key_here
LINKEDIN_CLIENT_ID=your_linkedin_client_id_here
FACEBOOK_APP_ID=your_facebook_app_id_here
```

## 🚀 Quick Start

### 1. Start the Service
```bash
# Development mode
uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8001 --workers 4
```

### 2. Access the API Documentation
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **Health Check**: http://localhost:8001/health

### 3. Test the Service
```bash
# Health check
curl http://localhost:8001/health

# Competitor analysis
curl -X POST "http://localhost:8001/ai/competitor-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "platform": "instagram",
    "competitor_handles": ["@competitor1", "@competitor2"],
    "analysis_type": "comprehensive"
  }'
```

## 🐳 Docker Deployment

### Using Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f ai-service

# Stop services
docker-compose down
```

### Manual Docker Build
```bash
# Build the image
docker build -t bloocube-ai-service .

# Run the container
docker run -p 8001:8001 --env-file .env bloocube-ai-service
```

## 📚 API Documentation

### Core Endpoints

#### Health Check
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system status
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe

#### Competitor Analysis
- `POST /ai/competitor-analysis` - Analyze competitor profiles
- `GET /ai/competitor-analysis/{analysis_id}` - Get analysis results

#### Content Suggestions
- `POST /ai/suggestions/hashtags` - Generate hashtag suggestions
- `POST /ai/suggestions/captions` - Generate caption suggestions
- `POST /ai/suggestions/posting-times` - Suggest optimal posting times
- `POST /ai/suggestions/content-ideas` - Generate content ideas

#### Matchmaking
- `POST /ai/matchmaking/brand-creator` - Match brands with creators
- `GET /ai/matchmaking/compatibility/{brand_id}/{creator_id}` - Get compatibility score

### Request/Response Examples

#### Competitor Analysis Request
```json
{
  "user_id": "user123",
  "platform": "instagram",
  "competitor_handles": ["@competitor1", "@competitor2"],
  "analysis_type": "comprehensive",
  "metrics": ["engagement_rate", "follower_growth", "content_performance"]
}
```

#### Content Suggestion Request
```json
{
  "user_id": "user123",
  "platform": "instagram",
  "content_type": "post",
  "topic": "fitness",
  "target_audience": "young_adults",
  "tone": "motivational"
}
```

## 🏗️ Project Structure

```
AI-services/
├── src/
│   ├── api/                    # FastAPI endpoints
│   │   ├── health.py          # Health check endpoints
│   │   ├── competitor.py      # Competitor analysis APIs
│   │   └── suggestions.py     # Content suggestion APIs
│   │
│   ├── core/                   # Core configuration
│   │   ├── config.py          # Environment variables & settings
│   │   ├── logger.py          # Structured logging setup
│   │   └── exceptions.py      # Custom error handling
│   │
│   ├── services/               # Business logic
│   │   ├── rag_service.py     # RAG pipeline implementation
│   │   ├── competitor_service.py # Competitor analysis logic
│   │   ├── nlp_utils.py       # NLP processing utilities
│   │   └── social/            # Social media integrations
│   │       ├── instagram.py
│   │       ├── youtube.py
│   │       ├── twitter.py
│   │       ├── linkedin.py
│   │       └── facebook.py
│   │
│   ├── pipelines/              # AI workflows
│   │   └── competitor_analysis.py # End-to-end analysis pipeline
│   │
│   ├── models/                 # AI model integrations
│   │   ├── llm_client.py      # OpenAI GPT integration
│   │   ├── embedding_model.py # Text embedding models
│   │   └── vector_store.py    # Vector database operations
│   │
│   ├── utils/                  # Utilities
│   │   ├── helpers.py         # Helper functions
│   │   ├── validators.py      # Input validation
│   │   └── constants.py       # Application constants
│   │
│   └── main.py                # FastAPI application entry point
│
├── tests/                      # Test suite
│   ├── test_competitor.py     # Competitor analysis tests
│   └── test_suggestions.py    # Content suggestion tests
│
├── scripts/                    # Data processing scripts
│   ├── embed_data.py          # Preprocess & embed data
│   └── sync_db.py             # Sync embeddings with database
│
├── requirements.txt           # Python dependencies
├── env.example               # Environment variables template
├── Dockerfile               # Container configuration
├── docker-compose.yml       # Multi-service orchestration
└── README.md               # This file
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_competitor.py

# Run with verbose output
pytest -v
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Performance Tests**: Load and stress testing
- **AI Model Tests**: Model accuracy and performance

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key for LLM access | - | Yes |
| `JWT_SECRET` | Secret key for JWT tokens | - | Yes |
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017/bloocube_ai` | Yes |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` | Yes |
| `VECTOR_DB_TYPE` | Vector database type (faiss/pinecone) | `faiss` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `DEBUG` | Debug mode | `false` | No |

### Feature Flags
- `ENABLE_COMPETITOR_ANALYSIS`: Enable competitor analysis features
- `ENABLE_CONTENT_SUGGESTIONS`: Enable content suggestion features
- `ENABLE_MATCHMAKING`: Enable brand-creator matchmaking
- `ENABLE_SOCIAL_MEDIA_INTEGRATION`: Enable social media API integrations

## 📊 Monitoring & Logging

### Logging
- **Structured Logging**: JSON-formatted logs with context
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Rotation**: Automatic rotation and compression
- **Context Tracking**: Request IDs and user context

### Metrics
- **API Metrics**: Request count, response times, error rates
- **AI Metrics**: Token usage, model performance, processing times
- **System Metrics**: CPU, memory, disk usage
- **Business Metrics**: Analysis counts, suggestion accuracy

### Health Checks
- **Liveness Probe**: Service is running
- **Readiness Probe**: Service is ready to accept requests
- **Dependency Checks**: Database and external service connectivity

## 🚀 Deployment

### Production Deployment

#### Using Docker Compose
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

#### Using Kubernetes
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/
```

#### Environment-Specific Configs
- **Development**: `docker-compose.yml`
- **Staging**: `docker-compose.staging.yml`
- **Production**: `docker-compose.prod.yml`

### Scaling
- **Horizontal Scaling**: Multiple service instances
- **Load Balancing**: Nginx or cloud load balancer
- **Database Scaling**: MongoDB replica sets
- **Cache Scaling**: Redis cluster

## 🔒 Security

### Authentication
- **JWT Tokens**: Secure API authentication
- **Role-Based Access**: Creator, Brand, Admin roles
- **API Key Management**: Secure key storage and rotation

### Data Protection
- **Input Validation**: Comprehensive input sanitization
- **Rate Limiting**: API rate limiting and throttling
- **Data Encryption**: Sensitive data encryption at rest
- **Audit Logging**: Complete audit trail

### Best Practices
- **Environment Variables**: No hardcoded secrets
- **HTTPS Only**: Secure communication
- **CORS Configuration**: Proper cross-origin settings
- **Security Headers**: Helmet.js security headers

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Standards
- **Python**: Follow PEP 8 guidelines
- **Type Hints**: Use type annotations
- **Documentation**: Docstrings for all functions
- **Testing**: Maintain test coverage > 80%

### Commit Convention
```
feat: add new feature
fix: bug fix
docs: documentation update
style: code formatting
refactor: code refactoring
test: add or update tests
chore: maintenance tasks
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- **API Docs**: http://localhost:8001/docs
- **Code Documentation**: Generated with Sphinx
- **Architecture Docs**: See `/docs` directory

### Getting Help
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Email**: support@bloocube.ai

### Common Issues

#### Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

#### Database Connection Issues
```bash
# Check MongoDB status
mongod --version

# Check Redis status
redis-cli ping
```

#### API Key Issues
```bash
# Verify environment variables
echo $OPENAI_API_KEY

# Check .env file
cat .env
