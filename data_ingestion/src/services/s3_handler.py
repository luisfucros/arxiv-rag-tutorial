import os
import logging
from typing import Optional
from botocore.exceptions import ClientError

if os.getenv("ENVIRONMENT") == "local":
    import localstack_client.session as boto3
else:
    import boto3


logger = logging.getLogger(__name__)


class S3Handler:
    def __init__(self, bucket_name: str, region_name: Optional[str] = None):
        """
        Initialize S3 handler.

        :param bucket_name: Target S3 bucket name
        :param region_name: AWS region (optional if configured globally)
        """
        self.bucket_name = bucket_name
        self.s3 = boto3.client("s3", region_name=region_name)

    def upload_file(self, local_path: str, s3_key: str) -> bool:
        """
        Upload a local file to S3.

        :param local_path: Path to local file
        :param s3_key: S3 object key
        """
        try:
            self.s3.upload_file(local_path, self.bucket_name, s3_key)
            logger.info("Uploaded file '%s' to bucket '%s' as '%s'",
                        local_path, self.bucket_name, s3_key)
            return True
        except ClientError as e:
            logger.error("Upload failed for '%s' to '%s/%s': %s",
                         local_path, self.bucket_name, s3_key, e, exc_info=True)
            return False

    def read_object(self, s3_key: str) -> Optional[bytes]:
        """
        Read object from S3 and return its bytes.

        :param s3_key: S3 object key
        """
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info("Read object '%s' from bucket '%s'",
                        s3_key, self.bucket_name)
            return response["Body"].read()
        except ClientError as e:
            logger.error("Read failed for '%s/%s': %s",
                         self.bucket_name, s3_key, e, exc_info=True)
            return None

    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download an S3 object to a local file.

        :param s3_key: S3 object key
        :param local_path: Local file destination
        """
        try:
            self.s3.download_file(self.bucket_name, s3_key, local_path)
            logger.info("Downloaded '%s/%s' to '%s'",
                        self.bucket_name, s3_key, local_path)
            return True
        except ClientError as e:
            logger.error("Download failed for '%s/%s' to '%s': %s",
                         self.bucket_name, s3_key, local_path, e, exc_info=True)
            return False

    def delete_object(self, s3_key: str) -> bool:
        """
        Delete object from S3.

        :param s3_key: S3 object key
        """
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info("Deleted object '%s' from bucket '%s'",
                        s3_key, self.bucket_name)
            return True
        except ClientError as e:
            logger.error("Delete failed for '%s/%s': %s",
                         self.bucket_name, s3_key, e, exc_info=True)
            return False
