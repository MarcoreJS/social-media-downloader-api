import re
import os
import uuid
import requests
from typing import Dict, List, Any, Optional
import yt_dlp
import instaloader
from typing import Optional
from urllib.parse import urlparse, parse_qs
from app.models.schemas import DownloadResponse
from app.services.downloader import MediaDownloader
from app.services.storage import S3StorageService
from app.utils.dir_utilities import find_media_files, clean_directory
import time
# from app.utils.exceptions import DownloadException

def get_story_media_id(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    story_media_id = query_params.get('story_media_id', [None])[0]
    return story_media_id


class InstagramDownloader(MediaDownloader):
    def __init__(self, storage_service: S3StorageService):
        self.storage_service = storage_service
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.session.headers.update(self.headers)
        self.instagram_pattern = re.compile(
            r'(https?://)?(www\.)?instagram\.com/(p|reel|tv|s|stories)/[a-zA-Z0-9_-]+/?'
        )

    def supports(self, url: str) -> bool:
        """Check if the URL is an Instagram post"""
        return bool(self.instagram_pattern.match(url))

    def download_legacy(self, url: str, download_dir: str) -> DownloadResponse:
        """Download Instagram media and upload to S3"""
        if not self.supports(url):
            raise Exception("Unsupported Instagram URL")

        try:
            # In a real implementation, you would use a proper Instagram API or library
            # This is a simplified example
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            shortcode = path.split('/')[-1]
            ig_type = path.split('/')[0]

            print(url)
            print(shortcode)
            L = instaloader.Instaloader(
                dirname_pattern=download_dir,
                filename_pattern='{shortcode}',
                save_metadata=False,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                compress_json=False,
                quiet=True,  # Hide verbose logs
                download_videos=True
            )

            username = "ml.marcoo"
            L.load_session_from_file(username, "/root/.config/instaloader/session-ml.marcoo")
            # L.load_session_from_file(username, "/Users/marcomercadolugo/Documents/code-projects/sm-downloader/api/session-ml.marcoo")
            print(L.context.username)
            # print(L.context)
            
            if ig_type == 's':
                # NOT WORKING
                print("highlights")
                media_id = get_story_media_id(url)
                print(media_id)
                post = instaloader.Post.from_mediaid(L.context, media_id)
                L.download_post(post, target=f"story_{media_id}")
            elif ig_type == 'stories':
                # NOT WORKING
                print("story")
                stories_info = []
                profile = instaloader.Profile.from_username(L.context, 'ningning.aespa_')

                for story in L.get_stories(userids=[profile.userid]):
                    for item in story.get_items():
                        try:
                            self.loader.download_storyitem(item, target=f'temp/{shortcode}')
                            stories_downloaded += 1
                            stories_info.append({
                                'date': item.date_utc.isoformat(),
                                'is_video': item.is_video,
                                'typename': item.typename
                            })
                        
                        except Exception as item_error:
                            print(f"Failed to download story item: {item_error}")
            else:
                print("post")
                post = instaloader.Post.from_shortcode(L.context, shortcode)
                
                # Determine media type and download
                if post.is_video:
                    print("video")
                    L.download_post(post, target=download_dir)
                    media_type = "video"
                else:
                    print("img")
                    L.download_post(post, target=download_dir)
                    media_type = "image"
            
            media_files = find_media_files(download_dir)
            download_urls = []
            # Generate S3 object name
            for media_file in media_files:
                object_name = f"instagram/{shortcode}/{media_file.split('/')[-1]}"
                print(media_file)
                print(object_name)
                # Upload to S3
                download_url = self.storage_service.upload_file(
                    media_file, object_name
                )
                download_urls.append(download_url)
            
            # clean_directory(f'temp/{shortcode}')

            return download_urls
        except Exception as e:
            raise Exception(f"Failed to download Instagram media: {str(e)}")

    def download(self, url: str, output_path="./temp/instagram") -> DownloadResponse:
        """
        Download instagram video without watermark using yt-dlp
        
        Args:
            url (str): instagram video URL
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
                'outtmpl': os.path.join(output_path + f"/{unique_id_str}", '%(id)s-%(autonumber)s.%(ext)s'),
                'writeinfojson': True,
                'writethumbnail': True,
                'extract_flat': False,
                # Try to force extraction of all media
                'playlistend': 20,  # Max items to extract
                'ignoreerrors': True,  # Continue on errors
                # 'format': 'best[height<=1080]',  # Download best quality up to 720p
                # 'noplaylist': True,
                # 'restrictfilenames': True
            }
            
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info
                info = ydl.extract_info(url, download=False)
                post_type = info.get('_type', 'N/A')
                post_id = info['id']
                # os.makedirs(output_path + f"/{unique_id_str}/{post_id}", exist_ok=True)
                print(f'INFO: {info}')
                print(f"Type: {info.get('extractor', 'unknown')}")
                print(f"Title: {info.get('title', 'N/A')}")
                print(f"Post Type: {info.get('_type', 'N/A')}")

                # Download the video
                if post_type == 'playlist':
                    print("Try with instaloader")
                    download_dir = f'temp/instagram/{unique_id_str}/{post_id}'
                    download_urls = self.download_legacy(url, download_dir)
                    clean_directory(f"temp/instagram/{unique_id_str}")
                    return DownloadResponse(
                        status="success",
                        download_url=download_urls,
                        media_type="image"
                    )
                else:
                    # Single item, download normally
                    ydl.download([url])
                
                    # Return the path to downloaded file
                    
                    filename = ydl.prepare_filename(info)

                    object_name = f'temp/instagram/{unique_id_str}.mp4'
                    download_url = self.storage_service.upload_file(
                        filename, object_name
                    )
                    media_type = "video"
                    clean_directory(f"temp/instagram/{unique_id_str}")
                    
                    return DownloadResponse(
                        status="success",
                        download_url=[download_url],
                        media_type="video" if 'video' in media_type else "image"
                    )
                    
        except Exception as e:
            print(f"Error downloading video: {str(e)}")
            raise Exception(f"Error downloading video: {str(e)}")
