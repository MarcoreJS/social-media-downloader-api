import boto3
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
            self.s3_client.upload_file(file_path, self.bucket_name, object_name)
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
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_bytes,
                ContentType=content_type
            )
            url = f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{object_name}"
            return url
        except ClientError as e:
            raise Exception(f"S3 upload failed: {str(e)}")