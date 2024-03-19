import os
import time
from google.cloud import firestore, storage


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "clipboard-service-account.json"

db = firestore.Client()
storage_client = storage.Client()

BUCKET_NAME = "clipboard-305915.appspot.com"


def get_users():
    """
    Returns a dictionary of the users collection.
    """
    backup = db.collection("users").stream()
    backup = list(backup)
    backup = {doc.id: doc.to_dict() for doc in backup}
    return backup


def upload_backup(backup):
    """
    Uploads a string representing the python dict
    of the users collection to the bucket.
    Returns the cloud file path for error checking.
    """
    bucket = storage_client.bucket(BUCKET_NAME)
    file_name = f"users-backups/users-backup-at-{time.time()}.txt"
    blob = bucket.blob(file_name)
    # Upload
    blob.upload_from_string(str(backup))
    print(f"{file_name} uploaded to bucket {BUCKET_NAME}")
    return file_name


def backup_exists(file_name):
    """
    Returns whether backup exists.
    """
    blobs = storage_client.list_blobs(BUCKET_NAME)
    for blob in blobs:
        if blob.name == file_name:
            return True
    return False


def backup_users(event, context):
    """
    Backs up users collection to bucket.
    """
    backup = get_users()
    file_name = upload_backup(backup)
    time.sleep(30)
    exists = backup_exists(file_name)
    if not exists:
        raise Exception("Backup not in bucket")
