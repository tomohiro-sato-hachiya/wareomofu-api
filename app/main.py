from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from .routers import \
    theme,\
    thesis,\
    user,\
    report,\
    favorite,\
    comment
from .sql import models
from .sql.database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

origins = []
postfix = 1
while f'FRONT_ORIGIN{postfix}' in os.environ:
    origin = os.environ[f'FRONT_ORIGIN{postfix}']
    origins.append(origin)
    postfix = postfix + 1

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(theme.router)
app.include_router(thesis.router)
app.include_router(user.router)
app.include_router(report.router)
app.include_router(favorite.router)
app.include_router(comment.router)

@app.get('/')
async def health_check():
    return True
