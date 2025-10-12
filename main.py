"""
Run script for Bloocube AI Services
Simple launcher: python run.py
"""
import uvicorn
import os
import sys

# Add the current directory to Python path so src module can be found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.core.config import settings
except Exception as e:
    print(f"Warning: Could not import settings ({e}), using defaults")
    # Fallback defaults if settings import fails
    class _Settings:
        ai_service_host = "0.0.0.0"
        ai_service_port = 8001
        log_level = "info"
    settings = _Settings()


def run():
    """Run the AI services application"""
    host = getattr(settings, "ai_service_host", "0.0.0.0")
    port = int(getattr(settings, "ai_service_port", 8001))
    log_level = str(getattr(settings, "log_level", "info")).lower()
    
    print(f"🚀 Starting Bloocube AI Services...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Docs: http://{host}:{port}/docs")
    print(f"   Health: http://{host}:{port}/health")
    print("")
    
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=True,  # Enable auto-reload for development
        reload_dirs=["src"],  # Only watch src directory
    )


if __name__ == "__main__":
    run()