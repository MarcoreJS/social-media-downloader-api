from pydantic import BaseModel, HttpUrl


class DownloadRequest(BaseModel):
    url: HttpUrl
    media_type: str = None  # Optional, can be auto-detected


class DownloadResponse(BaseModel):
    status: str
    download_url: str = None
    message: str = None
    media_type: str