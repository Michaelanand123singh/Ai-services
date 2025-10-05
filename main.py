"""
Launcher for Bloocube AI Services to allow: python main.py
"""
import uvicorn
try:
    from src.core.config import settings
except Exception:
    # Fallback defaults if settings import fails very early
    class _S:
        ai_service_host = "0.0.0.0"
        ai_service_port = 8001
        log_level = "info"
    settings = _S()


def run() -> None:
    uvicorn.run(
        "src.main:app",
        host=getattr(settings, "ai_service_host", "0.0.0.0"),
        port=int(getattr(settings, "ai_service_port", 8001)),
        log_level=str(getattr(settings, "log_level", "info")).lower(),
    )


if __name__ == "__main__":
    run()


