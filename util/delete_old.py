import os
import time
from google.cloud import firestore


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "clipboard-service-account.json"

db = firestore.Client()


def delete_old_clipboards(event, context):
    """
    Delete clipboards older than TTL from firestore.
    """
    TTL = 60 * 60 * 24 * 3
    backup = db.collection("clipboards").order_by("modified").stream()
    for document in backup:
        clipboard = document.to_dict()
        if clipboard["modified"] < (time.time() - TTL):
            print(document.id)
            document.reference.delete()
        else:
            # Descended past old clipboards in query list
            break
