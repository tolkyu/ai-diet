import uuid
from io import BytesIO
import aioboto3
from app.core.config import settings
from app.core.exceptions import StorageError
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageService:
    def __init__(self) -> None:
        self._session = aioboto3.Session(
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )

    def _get_client_kwargs(self) -> dict:
        kwargs: dict = {}
        if settings.s3_endpoint_url:
            kwargs["endpoint_url"] = settings.s3_endpoint_url
        return kwargs

    async def upload_photo(
        self, user_id: uuid.UUID, file_data: bytes, content_type: str = "image/jpeg"
    ) -> tuple[str, str]:
        key = f"photos/{user_id}/{uuid.uuid4()}.jpg"
        try:
            async with self._session.client("s3", **self._get_client_kwargs()) as s3:
                await s3.put_object(
                    Bucket=settings.s3_bucket_name,
                    Key=key,
                    Body=file_data,
                    ContentType=content_type,
                )
            url = f"https://{settings.s3_bucket_name}.s3.amazonaws.com/{key}"
            if settings.s3_endpoint_url:
                url = f"{settings.s3_endpoint_url}/{settings.s3_bucket_name}/{key}"
            return key, url
        except Exception as e:
            logger.error("S3 upload failed", key=key, error=str(e))
            raise StorageError(f"Failed to upload photo: {e}") from e

    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        try:
            async with self._session.client("s3", **self._get_client_kwargs()) as s3:
                url = await s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": settings.s3_bucket_name, "Key": key},
                    ExpiresIn=expires_in,
                )
            return url
        except Exception as e:
            raise StorageError(f"Failed to generate URL: {e}") from e

    async def delete_photo(self, key: str) -> None:
        try:
            async with self._session.client("s3", **self._get_client_kwargs()) as s3:
                await s3.delete_object(Bucket=settings.s3_bucket_name, Key=key)
        except Exception as e:
            logger.warning("S3 delete failed", key=key, error=str(e))
