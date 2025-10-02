# 🤖 Bloocube AI Services

AI-powered microservice for social media analysis, competitor research, content suggestions, and brand-creator matchmaking.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Google Cloud SDK (for deployment)
- MongoDB
- Redis

### Local Development

1. **Clone and setup**
   ```bash
   cd AI-services
   cp env.example .env
   # Edit .env with your API keys
   ```

2. **Using Docker Compose (Recommended)**
   ```bash
   docker-compose up -d
   ```

3. **Manual Setup**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn src.main:app --reload --port 8001
   ```

4. **Access the service**
   - API: http://localhost:8001
   - Documentation: http://localhost:8001/docs
   - Health Check: http://localhost:8001/health

## 🌐 GCP Deployment

### 1. Setup GCP Resources
```bash
# Make scripts executable (Linux/Mac)
chmod +x scripts/setup-gcp.sh
chmod +x deploy.sh

# Run GCP setup
./scripts/setup-gcp.sh YOUR_PROJECT_ID us-central1
```

### 2. Update Secrets
```bash
# Update secrets in Google Secret Manager
gcloud secrets versions add mongodb-url --data-file=- <<< "your-actual-mongodb-url"
gcloud secrets versions add openai-api-key --data-file=- <<< "your-actual-openai-key"
# ... update other secrets
```

### 3. Deploy to Cloud Run
```bash
./deploy.sh --project YOUR_PROJECT_ID --region us-central1
```

### 4. CI/CD Pipeline
The GitHub Actions workflow automatically:
- Runs tests and security scans
- Builds and pushes Docker images
- Deploys to staging/production
- Sets up monitoring and alerts

## 📊 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │  AI Services    │
│   (Next.js)     │───▶│   (Node.js)     │───▶│   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                       ┌─────────────────┐            │
                       │   Databases     │◀───────────┘
                       │ MongoDB + Redis │
                       └─────────────────┘
```

## 🔧 API Endpoints

### Core Services
- `POST /ai/competitor-analysis` - Analyze competitors
- `POST /ai/suggestions` - Generate content suggestions
- `POST /ai/matchmaking` - Brand-creator matching
- `POST /ai/trends` - Trend analysis
- `POST /ai/predictions` - Performance predictions

### Specialized Endpoints
- `POST /ai/suggestions/hashtags` - Hashtag suggestions
- `POST /ai/suggestions/captions` - Caption generation
- `POST /ai/suggestions/posting-times` - Optimal timing
- `POST /ai/suggestions/content-ideas` - Content ideas

### Utility Endpoints
- `GET /health` - Health check
- `GET /docs` - API documentation
- `GET /metrics` - Prometheus metrics

## 🔐 Environment Variables

Key environment variables (see `env.example` for complete list):

```bash
# Service Configuration
AI_SERVICE_PORT=8001
NODE_ENV=production

# Database
MONGODB_URL=mongodb://localhost:27017/bloocube
REDIS_URL=redis://localhost:6379/0

# AI Models
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4-turbo-preview

# Social Media APIs
TWITTER_API_KEY=your-twitter-key
YOUTUBE_API_KEY=your-youtube-key
# ... other social media APIs

# Security
JWT_SECRET=your-jwt-secret-must-match-backend
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test categories
pytest tests/test_competitor.py -v
pytest tests/test_suggestions.py -v
```

## 📊 Monitoring

### Local Monitoring Stack
```bash
# Start monitoring services
docker-compose up prometheus grafana

# Access dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin123)
```

### Production Monitoring
- **Metrics**: Prometheus + Google Cloud Monitoring
- **Logs**: Structured JSON logs to Google Cloud Logging
- **Alerts**: Email/Slack notifications for errors
- **Health Checks**: Automated uptime monitoring

## 🔄 Background Tasks

The service uses Celery for background processing:

```bash
# Start Celery worker
celery -A src.tasks.celery worker --loglevel=info

# Start Celery beat (scheduler)
celery -A src.tasks.celery beat --loglevel=info

# Monitor with Flower
celery -A src.tasks.celery flower
```

## 🛡️ Security

- **Authentication**: JWT tokens (shared with backend)
- **Rate Limiting**: Per-endpoint rate limits
- **Input Validation**: Pydantic models
- **Security Headers**: CORS, CSP, HSTS
- **Secrets Management**: Google Secret Manager
- **Container Security**: Non-root user, minimal image

## 📈 Performance

- **Caching**: Redis for API responses and embeddings
- **Async Processing**: FastAPI + asyncio
- **Connection Pooling**: Database connection optimization
- **Load Balancing**: Nginx reverse proxy
- **Auto Scaling**: Cloud Run automatic scaling

## 🔧 Development

### Code Quality
```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint code
flake8 src/ tests/

# Security scan
bandit -r src/
safety check
```

### Adding New Features

1. **Create API endpoint** in `src/api/`
2. **Add business logic** in `src/services/`
3. **Update models** in `src/models/`
4. **Add tests** in `tests/`
5. **Update documentation**

### Database Migrations
```bash
# Run database setup
python -m src.scripts.setup_db

# Create embeddings index
python -m src.scripts.create_embeddings
```

## 🚨 Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   ```bash
   # Check API key
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/models
   ```

2. **Database Connection Issues**
   ```bash
   # Test MongoDB connection
   mongosh $MONGODB_URL --eval "db.adminCommand('ping')"
   
   # Test Redis connection
   redis-cli -u $REDIS_URL ping
   ```

3. **Memory Issues**
   ```bash
   # Monitor memory usage
   docker stats
   
   # Increase memory limits in docker-compose.yml
   ```

### Logs
```bash
# View application logs
docker-compose logs -f ai-service

# View specific service logs
docker-compose logs -f celery-worker

# GCP Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision"
```

## 📚 Documentation

- **API Docs**: Available at `/docs` endpoint
- **Architecture**: See `docs/architecture.md`
- **Deployment**: See `docs/deployment.md`
- **Contributing**: See `CONTRIBUTING.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run quality checks
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: GitHub Issues
- **Documentation**: `/docs` endpoint
- **Email**: support@bloocube.com

---

**Built with ❤️ by the Bloocube Team**