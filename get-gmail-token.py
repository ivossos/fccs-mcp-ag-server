#!/usr/bin/env python3
"""
Gmail OAuth Token Generator
This script helps you generate a Gmail OAuth token for use with MCP servers.
"""

import os
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API scopes - adjust based on what you need
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',  # Read emails
    'https://www.googleapis.com/auth/gmail.send',      # Send emails
    'https://www.googleapis.com/auth/gmail.modify',    # Modify emails (mark as read, etc.)
]

def get_gmail_token(credentials_path: str, token_path: str) -> Credentials:
    """
    Generate or refresh Gmail OAuth token.
    
    Args:
        credentials_path: Path to credentials.json from Google Cloud Console
        token_path: Path where token.json will be saved
    
    Returns:
        Credentials object
    """
    creds = None
    
    # Check if token already exists
    if os.path.exists(token_path):
        print(f"Found existing token at: {token_path}")
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            print("Loaded existing credentials.")
        except Exception as e:
            print(f"Error loading existing token: {e}")
            print("Will generate a new token...")
            creds = None
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token expired. Refreshing...")
            try:
                creds.refresh(Request())
                print("Token refreshed successfully!")
            except Exception as e:
                print(f"Error refreshing token: {e}")
                print("Will generate a new token...")
                creds = None
        
        if not creds:
            print("\n" + "="*60)
            print("Starting OAuth flow...")
            print("A browser window will open for you to sign in.")
            print("="*60 + "\n")
            
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"Credentials file not found: {credentials_path}\n"
                    "Please download credentials.json from Google Cloud Console."
                )
            
            if not os.path.isfile(credentials_path):
                raise ValueError(
                    f"Path is not a file: {credentials_path}\n"
                    "Please provide the full path to credentials.json file."
                )
            
            # Validate JSON file can be read
            try:
                with open(credentials_path, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError:
                raise ValueError(
                    f"Invalid JSON file: {credentials_path}\n"
                    "Please make sure this is a valid credentials.json file from Google Cloud Console."
                )
            except PermissionError:
                raise PermissionError(
                    f"Permission denied: {credentials_path}\n"
                    "Please check file permissions or move the file to a location you have access to."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            
            # Run local server for OAuth flow
            creds = flow.run_local_server(port=0, open_browser=True)
            print("\n✓ Authorization successful!")
        
        # Save the credentials for the next run
        token_dir = os.path.dirname(token_path)
        if token_dir and not os.path.exists(token_dir):
            os.makedirs(token_dir, exist_ok=True)
            print(f"Created directory: {token_dir}")
        
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        
        print(f"✓ Token saved to: {token_path}")
    
    return creds

def main():
    """Main function to run the token generator."""
    print("="*60)
    print("Gmail OAuth Token Generator")
    print("="*60)
    print()
    
    # Get credentials path
    print("Step 1: Locate your credentials.json file")
    print("(Downloaded from Google Cloud Console)")
    print()
    credentials_path = input("Enter path to credentials.json: ").strip().strip('"')
    
    # Expand user path if needed
    credentials_path = os.path.expanduser(credentials_path)
    
    # Check if path exists
    if not os.path.exists(credentials_path):
        print(f"\n❌ Error: Path not found: {credentials_path}")
        print("\nPlease make sure:")
        print("1. You've downloaded credentials.json from Google Cloud Console")
        print("2. The path is correct (use full path like C:\\Users\\YourName\\credentials.json)")
        return
    
    # Check if it's a directory - if so, look for credentials.json in it
    if os.path.isdir(credentials_path):
        print(f"✓ Found directory: {credentials_path}")
        # Try to find credentials.json in the directory
        potential_file = os.path.join(credentials_path, "credentials.json")
        if os.path.exists(potential_file):
            print(f"✓ Found credentials.json in directory")
            credentials_path = potential_file
        else:
            print(f"\n❌ Error: The path is a directory, but credentials.json not found in it.")
            print(f"Looked for: {potential_file}")
            print("\nPlease provide the full path to the credentials.json file, for example:")
            print(f"  {potential_file}")
            return
    
    # Validate it's a file
    if not os.path.isfile(credentials_path):
        print(f"\n❌ Error: Path exists but is not a file: {credentials_path}")
        return
    
    # Validate it's a JSON file (basic check)
    if not credentials_path.lower().endswith('.json'):
        print(f"\n⚠ Warning: File doesn't have .json extension: {credentials_path}")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            return
    
    print(f"✓ Found credentials file: {credentials_path}")
    print()
    
    # Get token path
    print("Step 2: Choose where to save the token")
    default_token_path = os.path.join(
        os.path.dirname(credentials_path), 
        "token.json"
    )
    print(f"Default: {default_token_path}")
    token_path = input("Enter path to save token.json (or press Enter for default): ").strip().strip('"')
    
    if not token_path:
        token_path = default_token_path
    
    # Expand user path if needed
    token_path = os.path.expanduser(token_path)
    
    print(f"Token will be saved to: {token_path}")
    print()
    
    try:
        # Generate token
        creds = get_gmail_token(credentials_path, token_path)
        
        print()
        print("="*60)
        print("✓ SUCCESS! Token generated successfully!")
        print("="*60)
        print()
        print("Next steps:")
        print(f"1. Set environment variable GMAIL_CREDENTIALS_PATH = {credentials_path}")
        print(f"2. Set environment variable GMAIL_TOKEN_PATH = {token_path}")
        print("3. Restart Cursor")
        print()
        print("You can set environment variables by running:")
        print("  .\\set-gmail-env-vars.ps1")
        print()
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
    except PermissionError as e:
        print(f"\n❌ Permission Error: {e}")
        print("\nPossible solutions:")
        print("1. Move credentials.json to a location you have full access to (e.g., Documents folder)")
        print("2. Run PowerShell as Administrator")
        print("3. Check file permissions on the credentials file")
    except ValueError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Error generating token: {e}")
        print("\nCommon issues:")
        print("- Make sure you've enabled Gmail API in Google Cloud Console")
        print("- Verify your OAuth consent screen is configured")
        print("- Check that you've added your email as a test user")
        print("- Make sure the credentials.json file is valid and not corrupted")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

