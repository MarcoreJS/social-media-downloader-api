from fastapi import FastAPI
from app.routers import download


app = FastAPI(
    title="Social Media Downloader API",
    description="API for downloading media from social networks and storing in S3",
    version="0.1.0"
)

app.include_router(download.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}