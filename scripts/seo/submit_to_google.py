#!/usr/bin/env python3
"""
Google Indexing API Submission Script for AI Smart Home Hub

This script automatically submits newly published articles to Google's Indexing API
to ensure faster discovery and indexing of fresh content.

Usage:
    python scripts/seo/submit_to_google.py

Environment Variables:
    GOOGLE_SERVICE_ACCOUNT_JSON: Base64 encoded service account JSON
    SITE_DOMAIN: Your website domain (default: https://ai-smarthomehub.com)
"""

import json
import requests
import os
import glob
import datetime
import base64
import tempfile
from pathlib import Path

# Configuration
SITE_DOMAIN = os.getenv("SITE_DOMAIN", "https://ai-smarthomehub.com")
CONTENT_DIR = "content/articles"
SCOPES = ["https://www.googleapis.com/auth/indexing"]

def create_service_account_file():
    """Create temporary service account file from environment variable"""
    service_account_b64 = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not service_account_b64:
        print("❌ GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set")
        return None
    
    try:
        # Decode base64 service account JSON
        service_account_json = base64.b64decode(service_account_b64).decode('utf-8')
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_file.write(service_account_json)
        temp_file.flush()
        
        print(f"✅ Created temporary service account file: {temp_file.name}")
        return temp_file.name
    except Exception as e:
        print(f"❌ Error creating service account file: {e}")
        return None

def discover_today_articles():
    """Find articles published today"""
    today_str = datetime.datetime.today().strftime("%Y-%m-%d")
    yesterday_str = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Look for articles in content directory
    content_path = Path(CONTENT_DIR)
    if not content_path.exists():
        print(f"❌ Content directory not found: {CONTENT_DIR}")
        return []
    
    urls = []
    md_files = list(content_path.glob("**/*.md"))
    
    print(f"🔍 Scanning {len(md_files)} markdown files...")
    
    for path in md_files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Check if article was published today or yesterday
                if today_str in content or yesterday_str in content:
                    # Extract slug from filename
                    slug = path.stem
                    url = f"{SITE_DOMAIN}/articles/{slug}/"
                    urls.append(url)
                    print(f"📄 Found recent article: {slug}")
                    
        except Exception as e:
            print(f"⚠️ Error reading {path}: {e}")
            continue
    
    return urls

def discover_all_articles():
    """Find all published articles (fallback if no recent articles)"""
    content_path = Path(CONTENT_DIR)
    if not content_path.exists():
        return []
    
    urls = []
    md_files = list(content_path.glob("**/*.md"))
    
    # Limit to most recent 10 articles to avoid API limits
    md_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    for path in md_files[:10]:
        try:
            slug = path.stem
            url = f"{SITE_DOMAIN}/articles/{slug}/"
            urls.append(url)
        except Exception as e:
            print(f"⚠️ Error processing {path}: {e}")
            continue
    
    return urls

def push_to_google(urls, service_account_file):
    """Submit URLs to Google Indexing API"""
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import AuthorizedSession
    except ImportError:
        print("❌ Google Auth libraries not installed. Run: pip install google-auth google-auth-oauthlib")
        return False
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES)
        authed_session = AuthorizedSession(credentials)
        
        endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
        
        success_count = 0
        
        for url in urls:
            try:
                result = authed_session.post(endpoint, json={
                    "url": url,
                    "type": "URL_UPDATED"
                })
                
                if result.status_code == 200:
                    print(f"✅ Submitted: {url}")
                    success_count += 1
                else:
                    print(f"⚠️ Failed to submit {url}: Status {result.status_code}")
                    print(f"   Response: {result.text}")
                    
            except Exception as e:
                print(f"❌ Error submitting {url}: {e}")
                continue
        
        print(f"\n🎉 Successfully submitted {success_count}/{len(urls)} URLs to Google Indexing API")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Error with Google Indexing API: {e}")
        return False

def main():
    print("🚀 Google Indexing API Submission")
    print("=" * 50)
    
    # Create service account file from environment variable
    service_account_file = create_service_account_file()
    if not service_account_file:
        print("❌ Cannot proceed without service account credentials")
        return
    
    try:
        # First try to find today's articles
        urls = discover_today_articles()
        
        if not urls:
            print("📭 No articles published today, checking recent articles...")
            urls = discover_all_articles()
        
        if not urls:
            print("❌ No articles found to submit")
            return
        
        print(f"\n📊 Found {len(urls)} article(s) to submit:")
        for url in urls:
            print(f"  - {url}")
        
        # Submit to Google
        success = push_to_google(urls, service_account_file)
        
        if success:
            print("\n✅ Google Indexing API submission completed successfully!")
        else:
            print("\n❌ Google Indexing API submission failed")
        
    finally:
        # Clean up temporary service account file
        if service_account_file and os.path.exists(service_account_file):
            os.unlink(service_account_file)
            print(f"🧹 Cleaned up temporary service account file")

if __name__ == "__main__":
    main()