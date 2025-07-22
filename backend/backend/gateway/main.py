import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.gateway.api import router
from backend.gateway.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Doc Analyser API",
        description="Document analysis system using Claude Code",
        version="0.1.0",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(router, prefix="/api")

    return app


def main():
    uvicorn.run(
        "backend.gateway.main:create_app",
        host=settings.APP_HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        factory=True,
    )


if __name__ == "__main__":
    main()