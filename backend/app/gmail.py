"""
Gmail OAuth 2.0 and API integration for fetching emails and attachments.
"""

import base64
import logging
from datetime import datetime
from typing import Optional

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import httpx
from app.settings import settings

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def get_oauth_url(redirect_uri: str) -> str:
    """
    Generate OAuth consent URL for user authorization.
    Returns the URL the user should be redirected to.
    """
    flow = Flow.from_client_secrets_file(
        None,  # Use explicit credentials instead
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    ) if False else Flow.from_client_config(
        client_config={
            "installed": {
                "client_id": settings.gmail_client_id,
                "client_secret": settings.gmail_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    auth_url, state = flow.authorization_url(prompt='consent')
    return auth_url


def exchange_code(code: str, redirect_uri: str) -> dict:
    """
    Exchange OAuth authorization code for tokens.
    Returns {access_token, refresh_token, expiry, email}.
    """
    flow = Flow.from_client_config(
        client_config={
            "installed": {
                "client_id": settings.gmail_client_id,
                "client_secret": settings.gmail_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    flow.fetch_token(code=code)
    credentials = flow.credentials

    service = build('gmail', 'v1', credentials=credentials)
    profile = service.users().getProfile(userId='me').execute()
    email = profile.get('emailAddress', 'unknown')

    return {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        "email": email,
    }


def build_service(access_token: str, refresh_token: Optional[str] = None):
    """
    Build Gmail API service with given tokens.
    Handles token refresh if needed.
    """
    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.gmail_client_id,
        client_secret=settings.gmail_client_secret,
    )
    return build('gmail', 'v1', credentials=credentials)


async def fetch_new_messages(service, since_timestamp: datetime, max_results: int = 10) -> list[dict]:
    """
    Fetch new Gmail messages after the given timestamp.
    Returns list of message dicts with sender, subject, body, and attachments.
    """
    query = f"after:{int(since_timestamp.timestamp())}"
    messages = []

    try:
        logger.info(f"fetch_new_messages: querying Gmail since={since_timestamp.isoformat()} query={query!r}")
        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        message_ids = [m['id'] for m in results.get('messages', [])]
        logger.info(f"fetch_new_messages: found {len(message_ids)} message(s)")

        for msg_id in message_ids:
            msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            headers = msg['payload'].get('headers', [])
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'unknown')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(no subject)')

            body = ""
            attachments = []

            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        if 'data' in part['body']:
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    elif 'filename' in part and part['filename']:
                        attach_id = part['body'].get('attachmentId')
                        if attach_id:
                            attachment = service.users().messages().attachments().get(
                                userId='me', messageId=msg_id, id=attach_id
                            ).execute()
                            attachments.append({
                                "name": part['filename'],
                                "data": attachment.get('data', ''),
                                "mime": part.get('mimeType', 'application/octet-stream'),
                            })
            else:
                if 'data' in msg['payload']['body']:
                    body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')

            logger.info(
                f"fetch_new_messages: msg_id={msg_id} sender={sender!r} "
                f"subject={subject!r} attachments={len(attachments)}"
            )
            messages.append({
                "id": msg_id,
                "sender": sender,
                "subject": subject,
                "body": body,
                "attachments": attachments,
            })

    except Exception as e:
        logger.error(f"fetch_new_messages: error since={since_timestamp} error={e}", exc_info=True)

    return messages
