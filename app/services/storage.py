import boto3
import os
from urllib.parse import quote
from botocore.exceptions import ClientError
from app.config import settings
# from app.utils.exceptions import StorageException


class S3StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        self.bucket_name = settings.s3_bucket_name

    def upload_file(self, file_path: str, object_name: str) -> str:
        """Upload a file to S3 bucket"""
        try:

            filename = os.path.basename(object_name)
            
            # Properly encode filename for Content-Disposition header
            # This handles special characters and non-ASCII filenames
            encoded_filename = quote(filename)
            content_type = self.get_content_type(filename)
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                object_name,
                ExtraArgs={
                    'ContentType': content_type,
                    'ContentDisposition': f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_filename}',
                    # Optional: Set cache control
                    'CacheControl': 'no-cache, no-store, must-revalidate',
                    # Optional: Set other metadata
                    'Metadata': {
                        'original-filename': filename,
                        'uploaded-by': 'contentkeep'
                    }
                }
            )
            # url = f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{object_name}"
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_name},
                ExpiresIn=300
            )
            return presigned_url
        except ClientError as e:
            raise Exception(f"S3 upload failed: {str(e)}")

    def upload_bytes(self, file_bytes: bytes, object_name: str, content_type: str) -> str:
        """Upload bytes to S3 bucket"""
        try:
            if download_filename is None:
                download_filename = os.path.basename(object_name)
            
            # Properly encode filename for Content-Disposition (handles special characters)
            encoded_filename = quote(download_filename)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_bytes,
                ContentType=content_type,
                ContentDisposition=f'attachment; filename="{download_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            )
            url = f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{object_name}"
            return url
        except ClientError as e:
            raise Exception(f"S3 upload failed: {str(e)}")
        
    
    # Utility function to determine content type
    def get_content_type(self, filename):
        """
        Determine content type based on file extension
        """
        import mimetypes
        
        content_type, _ = mimetypes.guess_type(filename)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        return content_type