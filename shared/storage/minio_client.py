from minio import Minio
from minio.error import S3Error
from config.settings import settings


class MinioClient:

    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False
        )
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(settings.minio_bucket):
                self.client.make_bucket(settings.minio_bucket)
        except S3Error as e:
            print(f"Error creating bucket: {e}")

    def upload_file(self, file_path: str, file_data, content_type: str, size: int):
        try:
            self.client.put_object(
                settings.minio_bucket,
                file_path,
                file_data,
                size,
                content_type=content_type
            )
        except S3Error as e:
            raise Exception(f"Upload failed: {e}")

    def download_file(self, file_path: str):
        try:
            return self.client.get_object(settings.minio_bucket, file_path)
        except S3Error as e:
            raise Exception(f"Download failed: {e}")

    def delete_file(self, file_path: str):
        try:
            self.client.remove_object(settings.minio_bucket, file_path)
        except S3Error:
            pass


minio_client = MinioClient()