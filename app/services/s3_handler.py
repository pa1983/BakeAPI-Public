import io
from http import HTTPStatus
from urllib.parse import quote
from http.client import HTTPException

import boto3
import uuid as u

from fastapi import UploadFile

from app.core.config import settings
from app.core.logging_config import logger


def s3_client():
    try:
        session = boto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        s3 = session.resource('s3')
        bucket = s3.Bucket(settings.S3_BUCKET_NAME)
        s3_client = session.client('s3')
        return s3, bucket, s3_client
    except Exception as e:
        print(f'error getting s3 client: {e} - {e.args}')


# initialise once when server starts - does not expire
S3_SESSION, S3_BUCKET, S3_CLIENT = s3_client()


def push_UploadFile_to_s3(file: UploadFile, directory: str | None = None):
    file_obj = file.file
    uuid = u.uuid4().hex
    if directory:
        s3_key = f"{directory}/{uuid}"
    upload_fileobj_to_s3(file_obj, s3_key)
    return s3_key


def upload_fileobj_to_s3(file_object, s3_key):
    """
    Uploads a file-like object to S3
    :param file_object: any file-like object
    :param s3_key: unique ID, including any directory path required, e.g. images/{uuid}
    :return: None
    """
    try:
        S3_BUCKET.upload_fileobj(file_object, s3_key)

    except Exception as e:
        logger.exception(f'Error uploading {file_object} to s3.  review - {e}')
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


def delete_s3_object(s3_object_key):
    try:
        res = S3_BUCKET.Object(s3_object_key).delete()
        print(res)
        logger.info(f'Deleted {s3_object_key}')
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                            detail=f"File NOT deleted {s3_object_key}\n{str(e)}")


def get_psk(s3_object_key, friendly_filename=None, expiration=3600) -> str | None:
    """
    Use for downloading file objects that aren't accessible via cloudfront, e.g. private docs such as invoices
    Reduces data rounttrip time - user will download directly from S3, rather s3-api-api-client
    :param friendly_filename: actual file name and ext, to allow friendly nameing of downloaded file, rather than
    using the default of s3 key, whcih is a random UUID
    :param s3_object_key:
    :param expiration:
    :return:
    """
    if not friendly_filename:
        friendly_filename = s3_object_key
    encoded_filename = quote(friendly_filename)
    res = S3_CLIENT.generate_presigned_url('get_object',
                                           Params={'Bucket': settings.S3_BUCKET_NAME,
                                                   'Key': s3_object_key,
                                                   'ResponseContentDisposition': f'attachment; filename="{encoded_filename}"'},
                                           ExpiresIn=expiration)

    return res


def dl_fileobj(key):
    try:
        f = io.BytesIO()

        x = S3_BUCKET.download_fileobj(key, Fileobj=f)


    except Exception as e:
        logger.exception(f'Error downloading {key} from s3 - {e}')
        return False
    return f


class S3Client:
    """class to handle uploading images and docs to S3, and logging metadata to database"""

    def __init__(self):
        pass


if __name__ == '__main__':
    print(get_psk("invoice/3f5651b4f31540ba8dbae2f393a6d9c4", friendly_filename="invoice.pdf",
                  expiration=42300))  # 12 hour expiration
