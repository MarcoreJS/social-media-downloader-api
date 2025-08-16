from pydantic import BaseModel, HttpUrl
from typing import List

class DownloadRequest(BaseModel):
    url: HttpUrl
    media_type: str = None  # Optional, can be auto-detected

class DownloadUrl(BaseModel):
    url: str
    media_type: str

class DownloadResponse(BaseModel):
    status: str
    download_url: List[DownloadUrl] = None
    message: str = None
