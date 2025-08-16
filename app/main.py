from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import download


app = FastAPI(
    title="Social Media Downloader API",
    description="API for downloading media from social networks and storing in S3",
    version="0.1.0"
)

app.include_router(download.router)

origins = [
    "http://localhost:5173",
    "http://192.168.100.24:5173",
    "http://localhost:4173",
    "https://main.d1uaj1xrcxf3pb.amplifyapp.com",
    "https://contentkeep.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root_health_check():
    return {"status": "healthy"}