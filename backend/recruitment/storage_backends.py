from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class PublicMediaStorage(S3Boto3Storage):
    """Storage class for public media files."""

    location = settings.PUBLIC_MEDIA_LOCATION if hasattr(settings, "PUBLIC_MEDIA_LOCATION") else "media"
    default_acl = "private"
    file_overwrite = False
    custom_domain = False

