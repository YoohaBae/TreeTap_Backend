"""
GuROOM backend main.py
"""

import uvicorn
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from app import router as apps_router

tags_metadata = [
    {
        "name": "auth",
        "description": "Operations with authorization.",
    },
    {"name": "advertisements", "description": "Operations with advertisements"},
]
app = FastAPI(openapi_tags=tags_metadata)
app.include_router(apps_router, prefix="/apps")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://treetap.net",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def test():
    return JSONResponse({"message": "test"})


def run():
    uvicorn.run(app)


if __name__ == "__main__":
    run()
