from fastapi import FastAPI

from app.config import get_settings


def health() -> dict[str, str]:
    return {"status": "ok"}


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name)

    application.get("/health")(health)

    return application


app = create_app()
