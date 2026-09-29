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
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes under both /api and root for resilient routing across Vercel and local setups
app.include_router(api_router, prefix="/api")
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
