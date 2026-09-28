import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from backend.database.db import init_db, seed_demo_data
from backend.routes.api import router as api_router

# Initialize FastAPI App
app = FastAPI(
    title="SafiBot API",
    description="Backend API for SafiBot — AI & Knowledge-Driven Personalized College Assistant",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

@app.on_event("startup")
def on_startup():
    init_db()
    seed_demo_data()
    print("SafiBot Backend started: SQLite initialized and demo data ready.")

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "SafiBot College Assistant API",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
