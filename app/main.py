from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core.config import settings
from app.database.session import engine, Base
from app.api.v1.api import api_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

templates.env.cache = None

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse(name="index.html", context={"request": request})
