import time
import os
import uuid

from google.cloud import firestore
from werkzeug.security import generate_password_hash, check_password_hash
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "clipboard-service-account.json"

db = firestore.Client()


def register(email, password):
    """
    Create new user.
    """
    MAX_LENGTH = 512
    email = email.lower()[:MAX_LENGTH + 1].strip()
    password = password[:MAX_LENGTH + 1]

    doc_ref = db.collection(u"users").document(f"{email}")

    # Make sure not already registered
    doc = doc_ref.get()
    if doc.exists:
        return False

    # Create new user
    hash = generate_password_hash(password)
    doc_ref.set({
        u"hash": hash,
        U"token": str(uuid.uuid4()),
        u"email_token": "not verified",
        u"created": time.time(),
    })
    return True


def user_exists(email):
    """
    Verify credentials.
    """
    if not email:
        return False

    email = email.lower().strip()

    doc_ref = db.collection(u"users").document(f"{email}")

    # Make user exists
    doc = doc_ref.get()
    return doc.exists


def verify_login(email, password):
    """
    Verify credentials.
    """

    email = email.lower().strip()

    doc_ref = db.collection(u"users").document(f"{email}")

    # Make user exists
    doc = doc_ref.get()
    if not doc.exists:
        return False

    hash = doc.to_dict()["hash"]
    if not check_password_hash(hash, password):
        return False

    return True


def email_confirmed(email):
    """
    Check if email has been confirmed with the link.
    """

    email = email.lower().strip()

    doc_ref = db.collection(u"users").document(f"{email}")
    doc = doc_ref.get()

    if doc.to_dict()["email_token"] == "verified":
        return True

    return False


def get_token(email):
    """
    Get token for oauth and api.
    """

    email = email.lower().strip()

    if not email_confirmed(email):
        # Make sure email has been confirmed
        return False

    doc_ref = db.collection(u"users").document(f"{email}")

    # Make user exists
    doc = doc_ref.get()
    if not doc.exists:
        return False

    return doc.to_dict()["token"]


def verify_token(email, token):
    """
    Verify token for oauth and api.
    """

    email = email.lower().strip()

    doc_ref = db.collection(u"users").document(f"{email}")

    # Make user exists
    doc = doc_ref.get()
    if not doc.exists:
        return False

    if token == doc.to_dict()["token"]:
        return True

    return False


def refresh_token(email):
    """
    Refresh token.
    """

    email = email.lower().strip()

    doc_ref = db.collection(u"users").document(f"{email}")

    doc_ref.update({
        u"token": str(uuid.uuid4()),
    })
    return True


def update_password(email, password):
    """
    Update password.
    """

    email = email.lower().strip()

    doc_ref = db.collection(u"users").document(f"{email}")

    hash = generate_password_hash(password)
    doc_ref.update({
        u"hash": hash,
    })

    # Refresh token for api and oauth
    refresh_token(email)

    return True


def delete_account(email):
    """
    Delete account.
    """

    email = email.lower().strip()

    doc_ref = db.collection(u"users").document(f"{email}")
    doc = doc_ref.get()
    if doc.exists:
        doc_ref.delete()

    doc_ref = db.collection(u"clipboards").document(f"{email}")
    doc = doc_ref.get()
    if doc.exists:
        doc_ref.delete()


def read(email):
    """
    Returns a dictionary of
    the clipboard.
    """
    EMPTY_CLIPBOARD = {"contents": "Clipboard empty: paste something!",
                       "modified": time.time(),
                       }

    email = email.lower().strip()

    doc_ref = db.collection(u"clipboards").document(f"{email}")
    doc = doc_ref.get()

    if not doc.exists:
        return EMPTY_CLIPBOARD

    doc = doc.to_dict()
    clipboard = {"contents": doc["contents"],
                 "modified": doc["modified"],
                 }

    if clipboard["contents"].strip() == "":
        return EMPTY_CLIPBOARD

    # 3 days
    CLIPBOARD_DURATION = 3 * 24 * 60 * 60
    if clipboard["modified"] < (time.time() - CLIPBOARD_DURATION):
        return EMPTY_CLIPBOARD

    return clipboard


def set(email, contents):
    """
    Sets new clipboard value in firestore.
    """

    email = email.lower().strip()

    MAX_LENGTH = 100000
    # Limit size of clipboard
    contents = str(contents)[:MAX_LENGTH + 1]
    doc_ref = db.collection(u"clipboards").document(f"{email}")
    doc_ref.set({
        u"contents": contents,
        u"modified": time.time(),
    })


def send_password_reset(email):

    email = email.lower().strip()

    doc_ref = db.collection(u"users").document(f"{email}")
    doc = doc_ref.get().to_dict()
    # Reset token lasts for 24 hours
    RESET_TOKEN_DURATION = 60 * 60 * 24
    if "reset_timestamp" in doc and doc["reset_timestamp"] > time.time() - RESET_TOKEN_DURATION:
        # Extend deadline of token if not expired
        token = doc["reset_token"]
    else:
        token = str(uuid.uuid4())

    doc_ref.update({
        u"reset_token": token,
        u"reset_timestamp": time.time()
    })

    message = Mail(
        from_email=("website@myclipboard.io", "My Clipboard"),
        to_emails=email,
        subject="My Clipboard: Reset Password",
    )
    message.dynamic_template_data = {
        "email": email,
        "token": token,
        "time": int(time.time()),
    }
    message.template_id = "d-344fc5ddd04246e8bbb650603a83a5a0"
    sendgrid_client = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
    sendgrid_client.send(message)


def validate_reset_token(email, token):

    email = email.lower().strip()

    if not user_exists(email):
        return False

    doc_ref = db.collection(u"users").document(f"{email}")
    doc = doc_ref.get()
    doc = doc.to_dict()

    # Reset token lasts for 24 hours
    RESET_TOKEN_DURATION = 60 * 60 * 24

    if token == doc["reset_token"] and time.time() < int(doc["reset_timestamp"]) + RESET_TOKEN_DURATION:
        # Set confirm email to verified as well
        # since user must have access to email
        doc_ref.update({
            u"email_token": "verified"
        })
        return True

    return False


def send_confirm_email(email):

    email = email.lower().strip()

    doc_ref = db.collection(u"users").document(f"{email}")
    token = str(uuid.uuid4())
    doc_ref.update({
        u"email_token": token
    })

    message = Mail(
        from_email=("website@myclipboard.io", "My Clipboard"),
        to_emails=email,
        subject="My Clipboard: Confirm Email",
    )
    message.dynamic_template_data = {
        "email": email,
        "token": token,
        "time": int(time.time()),
    }
    message.template_id = "d-161a1ed4dad448b8b44d0e3a0f9987b1"
    sendgrid_client = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
    sendgrid_client.send(message)


def validate_email_token(email, token):
    """
    If email confirmation token matches database,
    verify user in database.
    """

    email = email.lower().strip()

    if not user_exists(email):
        return False

    doc_ref = db.collection(u"users").document(f"{email}")
    doc = doc_ref.get()
    doc = doc.to_dict()

    if token == doc["email_token"]:
        doc_ref.update({
            u"email_token": "verified"
        })
        return True

    return False
