from fastapi import APIRouter, HTTPException
from app.models.schemas import DownloadRequest, DownloadResponse
from app.services.downloader import MediaDownloader
from app.services.instagram import InstagramDownloader
from app.services.tiktok import TikTokDownloader
from app.services.storage import S3StorageService
# from app.utils.exceptions import DownloadException


router = APIRouter(prefix="/download", tags=["download"])

# Initialize services
storage_service = S3StorageService()
downloaders: list[MediaDownloader] = [
    InstagramDownloader(storage_service),
    TikTokDownloader(storage_service)
    # Add other downloaders here as they're implemented
]


@router.post("/", response_model=DownloadResponse)
async def download_media(request: DownloadRequest):
    """Download media from a social media URL and upload to S3"""
    url = str(request.url)
    
    # Find a downloader that supports this URL
    downloader = next((d for d in downloaders if d.supports(url)), None)
    
    if not downloader:
        raise HTTPException(
            status_code=400,
            detail="Unsupported URL. Currently only Instagram and TikTok is supported."
        )
    
    # try:
    return downloader.download(url)
    # except Exception as e:
    #     print(e)
    #     raise HTTPException(status_code=400, detail=str(e))