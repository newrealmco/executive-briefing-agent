"""
One-time script to generate Gmail OAuth2 refresh token.

Run locally before setting up GitHub secrets:
  python scripts/gmail_auth.py

Prerequisites:
  1. Create OAuth 2.0 credentials in Google Cloud Console
     (type: Desktop App, scope: gmail.readonly)
  2. Download credentials.json and place in project root
  3. Run this script — it will open a browser for consent
  4. Copy the printed refresh_token into your GitHub secret GMAIL_REFRESH_TOKEN
"""
import json
import os
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDS_FILE = Path(__file__).parent.parent / "credentials.json"


def main():
    if not CREDS_FILE.exists():
        print(f"ERROR: {CREDS_FILE} not found.")
        print("Download OAuth2 Desktop credentials from Google Cloud Console.")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n=== Gmail OAuth2 tokens ===")
    print(f"client_id:     {creds.client_id}")
    print(f"client_secret: {creds.client_secret}")
    print(f"refresh_token: {creds.refresh_token}")
    print("\nStore these as GitHub secrets:")
    print("  GMAIL_CLIENT_ID     →", creds.client_id)
    print("  GMAIL_CLIENT_SECRET →", creds.client_secret)
    print("  GMAIL_REFRESH_TOKEN →", creds.refresh_token)


if __name__ == "__main__":
    main()
