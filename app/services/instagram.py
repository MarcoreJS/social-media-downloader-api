import re
import requests
import instaloader
from typing import Optional
from urllib.parse import urlparse, parse_qs
from app.models.schemas import DownloadResponse
from app.services.downloader import MediaDownloader
from app.services.storage import S3StorageService
from app.utils.dir_utilities import find_media_files, clean_directory
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
        self.instagram_pattern = re.compile(
            r'(https?://)?(www\.)?instagram\.com/(p|reel|tv|s|stories)/[a-zA-Z0-9_-]+/?'
        )

    def supports(self, url: str) -> bool:
        """Check if the URL is an Instagram post"""
        return bool(self.instagram_pattern.match(url))

    def download(self, url: str) -> DownloadResponse:
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
                dirname_pattern=f'temp/{shortcode}',
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
            # L.load_session_from_file(username, "/root/.config/instaloader/session-ml.marcoo")
            L.load_session_from_file(username, "/Users/marcomercadolugo/Documents/code-projects/sm-downloader/api/session-ml.marcoo")
            print(L.context.username)
            print(L.context)
            
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
                stories_owner = path.split('/')[1]
                print(stories_owner)
                profile = instaloader.Profile.from_username(L.context, stories_owner)
                print(profile.username)
                print(profile.userid)
                L.download_stories(userids=[profile.userid])
            else:
                print("post")
                post = instaloader.Post.from_shortcode(L.context, shortcode)
                
                # Determine media type and download
                if post.is_video:
                    print("video")
                    L.download_post(post, target='temp')
                    media_type = "video"
                else:
                    print("img")
                    L.download_post(post, target='temp')
                    media_type = "image"
            
            media_files = find_media_files(f"temp/{shortcode}/")
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
            
            clean_directory(f'temp/{shortcode}')

            return DownloadResponse(
                status="success",
                download_url=download_urls,
                media_type="video" if 'video' in media_type else "image"
            )
        except Exception as e:
            raise Exception(f"Failed to download Instagram media: {str(e)}")

    # def _fetch_media(self, url: str) -> tuple[bytes, str]:
    #     """Fetch media from Instagram (simplified example)"""
    #     # NOTE: In a real implementation, you would:
    #     # 1. Use Instagram API or a reliable library
    #     # 2. Handle authentication if needed
    #     # 3. Properly extract media URLs from the post
    #     # 4. Download the highest quality version
        
    #     # This is a placeholder implementation
    #     response = self.session.get(url)
    #     response.raise_for_status()
        
    #     # Determine if it's a video or image (simplified)
    #     is_video = '/reel/' in url or '/tv/' in url
    #     content_type = 'video/mp4' if is_video else 'image/jpeg'
        
    #     # Return dummy data - replace with actual media download
    #     dummy_data = b'dummy_data'  # Replace with actual media bytes
    #     return dummy_data, content_type