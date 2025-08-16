import re
import requests
import yt_dlp
import uuid
import json
import os
from typing import Optional
from urllib.parse import urlparse, parse_qs
from app.models.schemas import DownloadResponse, DownloadUrl
from app.services.downloader import MediaDownloader
from app.services.storage import S3StorageService
from app.utils.dir_utilities import clean_directory, find_media_files



class TikTokDownloader(MediaDownloader):
    def __init__(self, storage_service: S3StorageService):
        self.storage_service = storage_service
        self.session = requests.Session()
        self.id_method = "uuid"
        self.output_path = ""
        self.tiktok_patterns = [
            r'^https://www\.tiktok\.com/@[^/]+/video/\d+',  # Standard TikTok video URL
            r'^https://vm\.tiktok\.com/[^/]+/',             # TikTok vm short URL
            r'^https://vt\.tiktok\.com/[^/]+/',             # TikTok vt short URL
            # Standard YouTube video URLs
            r'^https?://(www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})(&.*)?',
            
            # YouTube shortened URLs (youtu.be)
            r'^https?://(www\.)?youtu\.be/([a-zA-Z0-9_-]{11})(\?.*)?',
            
            # YouTube Shorts URLs
            r'^https?://(www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})(\?.*)?',
            
            # YouTube embed URLs
            r'^https?://(www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})(\?.*)?',
            
            # YouTube mobile URLs (m.youtube.com)
            r'^https?://m\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})(&.*)?',
            
            # YouTube mobile shorts
            r'^https?://m\.youtube\.com/shorts/([a-zA-Z0-9_-]{11})(\?.*)?',
            
            # YouTube nocookie embed URLs
            r'^https?://(www\.)?youtube-nocookie\.com/embed/([a-zA-Z0-9_-]{11})(\?.*)?'
        ]
        self.download_log = []
        
        # Headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def supports(self, url: str) -> bool:
        """Check if the URL is an Instagram post"""
        return any(re.match(pattern, url) for pattern in self.tiktok_patterns)
    
    def download(self, url: str, output_path="./temp/tiktok") -> DownloadResponse:
        """
        Download TikTok video without watermark using yt-dlp
        
        Args:
            url (str): TikTok video URL
            output_path (str): Directory to save the video
        
        Returns:
            str: Path to downloaded file or None if failed
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_path, exist_ok=True)


            unique_id_str = str(uuid.uuid4())
            print("============== VIDEO POST ==============")
            # Configure yt-dlp options
            ydl_opts = {
                'outtmpl': os.path.join(output_path + f"/{unique_id_str}", '%(title)s.%(ext)s'),
                'format': 'best[height<=1080]',  # Download best quality up to 720p
                'noplaylist': True,
                'restrictfilenames': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info
                info = ydl.extract_info(url, download=False)
                print(f'INFO: {info}')
                duration = info.get('duration')
                print(f'Duration {duration} seconds')

                if 900 < duration:
                    return DownloadResponse(
                        status='FAILED',
                        download_url=[],
                        message= f"Videos longer than 15 min aren't allowed."
                    )  
                # Download the video
                ydl.download([url])
                
                # Return the path to downloaded file
                
                filename = ydl.prepare_filename(info)

                object_name = f'temp/tiktok/{unique_id_str}.mp4'
                dwn_url_str = self.storage_service.upload_file(
                    filename, object_name
                )
                download_url = DownloadUrl(url=dwn_url_str, media_type='video')
                
                clean_directory(f"temp/tiktok/{unique_id_str}")
                
                return DownloadResponse(
                    status="success",
                    download_url=[download_url]
                )
                    
        except Exception as e:
            print(f"Error downloading video: {str(e)}")

        
    def get_post_data(self, url):
        """Extract post data from TikTok URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Extract JSON data from the page
            json_pattern = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>'
            match = re.search(json_pattern, response.text)
            
            if match:
                json_data = json.loads(match.group(1))
                return json_data
            
            # Alternative pattern for newer TikTok versions
            json_pattern2 = r'window\[\"SIGI_STATE\"\]\s*=\s*({.*?});'
            match2 = re.search(json_pattern2, response.text)
            
            if match2:
                json_data = json.loads(match2.group(1))
                return json_data
                
            return None
        except Exception as e:
            print(f"Error getting post data: {e}")
            return None

    def is_image_post(self, post_data):
        """Determine if the post contains images instead of video"""
        try:
            # Navigate through the JSON structure to find media info
            # This structure may vary, so we check multiple possible paths
            print("=================== POST DATA ===============")
            with open('post_data.json', 'w') as file:
                file.write(json.dumps(post_data))
            
            # Method 1: Check for image collections
            if 'ItemList' in post_data.get('__DEFAULT_SCOPE__', {}):
                items = post_data['__DEFAULT_SCOPE__']['ItemList']
                for item_id, item_data in items.items():
                    if 'imagePost' in item_data:
                        return True
                    if item_data.get('mediaType') == 2:  # 2 typically means image
                        return True
            
            # Method 2: Check webapp data
            if 'webapp.video-detail' in post_data.get('__DEFAULT_SCOPE__', {}):
                video_detail = post_data['__DEFAULT_SCOPE__']['webapp.video-detail']
                if 'itemInfo' in video_detail:
                    item_info = video_detail['itemInfo']['itemStruct']
                    if 'imagePost' in item_info:
                        return True
                    if item_info.get('mediaType') == 2:
                        return True
                    
            if 'seo.abtest' in post_data.get('__DEFAULT_SCOPE__', {}):
                full_url = post_data['__DEFAULT_SCOPE__']['seo.abtest']['canonical']
                if full_url.split('/')[-2] == 'photo':
                    return True
                else:
                    return False
            
            return False
            
        except Exception as e:
            print(f"Error checking post type: {e}")
            return False
