from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class MediaStorage(S3Boto3Storage):
    """
    Custom storage backend to handle media files with S3.
    """
    location = settings.MEDIAFILES_LOCATION
    file_overwrite = False
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN

    def url(self, name):
        """
        Generate the full URL for a given file name stored in S3.
        Ensures the URL includes the correct location prefix and custom
        domain.
        """
        if not name.startswith(self.location):
            name = f"{self.location}/{name}"
        return f"https://{self.custom_domain}/{name}"
