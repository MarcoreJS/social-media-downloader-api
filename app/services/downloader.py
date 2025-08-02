from abc import ABC, abstractmethod
from typing import Optional
from app.models.schemas import DownloadResponse


class MediaDownloader(ABC):
    """Abstract base class for media downloaders"""
    
    @abstractmethod
    def download(self, url: str) -> DownloadResponse:
        """Download media from the given URL"""
        pass
    
    @abstractmethod
    def supports(self, url: str) -> bool:
        """Check if this downloader supports the given URL"""
        pass