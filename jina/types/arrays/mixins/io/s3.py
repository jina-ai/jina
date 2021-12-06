import os
from typing import Union
from urllib.parse import urlparse

from jina.logging.logger import JinaLogger

from .....excepts import InvalidS3URL, InvalidAWSCredentials
from .....importer import ImportExtensions


def validate_envs(func):
    """Raise if aws envs are not set

    :param func: function to be invoked
    :return: decorator for env check
    """

    def wrapper(self, *args, **kwargs):
        if (
            'AWS_ACCESS_KEY_ID' not in os.environ
            or 'AWS_SECRET_ACCESS_KEY' not in os.environ
        ):
            raise InvalidAWSCredentials(
                'AWS credentials are not set. Please set '
                '`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`'
            )
        else:
            return func(self, *args, **kwargs)

    return wrapper


class S3URLMeta(type):
    """Metaclass for S3URL instance check"""

    @classmethod
    def __instancecheck__(cls, __instance) -> bool:
        return urlparse(__instance, allow_fragments=False).scheme == 's3'


class S3URL(metaclass=S3URLMeta):
    """class to define S3 URLs"""

    def __init__(self, url):
        if not isinstance(url, type(self)):
            raise InvalidS3URL(f'Invalid url {url} passed')

        self._url = urlparse(url, allow_fragments=False)
        with ImportExtensions(required=True):
            import boto3

        self.client = boto3.client('s3')
        self.logger = JinaLogger(self.__class__.__name__)

    @property
    def bucket(self):
        """bucket name property

        :return: bucket name of current url
        """
        return self._url.netloc

    @property
    def key(self):
        """key name property

        :return: key name of current url
        """
        if self._url.query:
            return self._url.path.lstrip('/') + '?' + self._url.query
        else:
            return self._url.path.lstrip('/')

    @property
    def url(self):
        """url property

        :return: url
        """
        return self._url.geturl()

    @property
    def bucket_exists(self) -> bool:
        """Check if bucket exists on remote

        :return: True if bucket exists
        """
        try:
            response = self.client.head_bucket(Bucket=self.bucket)
            return response['ResponseMetadata']['HTTPStatusCode'] == 200
        except:
            return False

    @validate_envs
    def write(self, content: Union[bytes, str]):
        """Create an object on a S3 bucket

        :param content: content to be uploaded
        """
        if self.bucket_exists:
            self.client.put_object(Body=content, Bucket=self.bucket, Key=self.key)
        else:
            self.logger.error(f'bucket doesn\'t exist. nothing to do')

    @validate_envs
    def read(self) -> bytes:
        """Download an object from a S3 bucket

        :return: content on the S3 bucket
        """
        if self.bucket_exists:
            response = self.client.get_object(Bucket=self.bucket, Key=self.key)
            return response['Body'].read()
        else:
            self.logger.error(f'bucket doesn\'t exist. nothing to do')

    @validate_envs
    def delete(self):
        """Delete an object from a S3 bucket"""
        if self.bucket_exists:
            self.client.delete_object(Bucket=self.bucket, Key=self.key)
