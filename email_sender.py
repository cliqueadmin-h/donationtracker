#!/usr/bin/env python3
"""
Email functionality for the Donation Opportunities Finder

This module handles sending email reports with donation opportunities
using Gmail API v1.
"""

import json
import os
import base64
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False


class EmailSender:
    """Email sender for donation opportunities results using Gmail API"""
    
    # Gmail API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.readonly'
    ]
    
    def __init__(self, config_path='config.json'):
        """Initialize email sender with configuration"""
        self.config = self._load_config(config_path)
        self.email_config = self.config.get('email_settings', {})
        self.service = None
        
    def _load_config(self, config_path):
        """Load configuration from file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print("Warning: config.json is not valid JSON. Using defaults.")
            return {}
    
    def _get_gmail_service(self):
        """Authenticate and get Gmail API service"""
        if not GMAIL_API_AVAILABLE:
            raise ImportError("Gmail API dependencies not installed. Run: pip install google-auth google-auth-oauthlib google-api-python-client")
        
        creds = None
        
        # Load existing credentials
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                # Check for credentials file
                credentials_file = 'credentials.json'
                if not os.path.exists(credentials_file):
                    raise FileNotFoundError(
                        f"Gmail API credentials file '{credentials_file}' not found.\n"
                        "Please download it from Google Cloud Console and place it in the project directory.\n"
                        "See setup instructions in README.md"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, self.SCOPES)
                # Use run_console() instead of run_local_server() to avoid port issues
                creds = flow.run_console()
            
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        return build('gmail', 'v1', credentials=creds)
    
    def _create_message(self, sender, to, subject, message_content, attachments=None):
        """Create a message for an email"""
        message = MIMEMultipart('alternative')
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        
        # Add message body (both text and HTML versions)
        if isinstance(message_content, dict):
            if 'text' in message_content:
                text_part = MIMEText(message_content['text'], 'plain', 'utf-8')
                message.attach(text_part)
            if 'html' in message_content:
                html_part = MIMEText(message_content['html'], 'html', 'utf-8')
                message.attach(html_part)
        else:
            text_part = MIMEText(str(message_content), 'plain', 'utf-8')
            message.attach(text_part)
        
        # Add attachments
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    filename = os.path.basename(file_path)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}',
                    )
                    message.attach(part)
        
        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw_message}
    
    def _send_message(self, service, user_id, message):
        """Send an email message"""
        try:
            message = service.users().messages().send(userId=user_id, body=message).execute()
            return message
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def _create_html_report(self, places, search_info):
        """Create an HTML email report"""
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .place {{ background-color: #ffffff; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 15px; }}
                .place-name {{ color: #2c3e50; font-size: 18px; font-weight: bold; margin-bottom: 8px; }}
                .place-info {{ color: #666; margin: 5px 0; }}
                .rating {{ color: #f39c12; font-weight: bold; }}
                .address {{ color: #7f8c8d; }}
                .email {{ color: #27ae60; font-weight: bold; }}
                .phone {{ color: #3498db; }}
                .reviews {{ margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee; }}
                .review {{ margin: 10px 0; padding: 8px; background-color: #f8f9fa; border-radius: 4px; }}
                .review-author {{ font-weight: bold; color: #2c3e50; }}
                .review-rating {{ color: #f39c12; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 2px solid #eee; color: #7f8c8d; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🎯 Donation Opportunities Found</h2>
                <p><strong>Search Details:</strong></p>
                <ul>
                    <li><strong>Search Type:</strong> {search_info.get('type', 'Unknown')}</li>
                    <li><strong>Location:</strong> {search_info.get('location', 'Unknown')}</li>
                    <li><strong>Keywords:</strong> {search_info.get('keywords', 'N/A')}</li>
                    <li><strong>Results Found:</strong> {len(places)} organizations</li>
                    <li><strong>Generated:</strong> {timestamp}</li>
                </ul>
            </div>
        """
        
        for i, place in enumerate(places, 1):
            rating_value = place.get('rating') or 0
            rating_stars = "⭐" * int(rating_value) if rating_value else ""
            rating_text = f"{place.get('rating', 'N/A')} {rating_stars}" if place.get('rating') else "No rating"
            
            html += f"""
            <div class="place">
                <div class="place-name">{i}. {place.get('name', 'Unknown Name')}</div>
                <div class="place-info rating">⭐ Rating: {rating_text}</div>
                <div class="place-info address">📍 Address: {place.get('address', 'Address not available')}</div>
            """
            
            if place.get('phone'):
                html += f'<div class="place-info phone">📞 Phone: {place.get("phone")}</div>'
            
            if place.get('email'):
                html += f'<div class="place-info email">📧 Email: {place.get("email")}</div>'
            
            if place.get('website'):
                html += f'<div class="place-info">🌐 Website: <a href="{place.get("website")}">{place.get("website")}</a></div>'
            
            if place.get('distance_miles'):
                html += f'<div class="place-info">📏 Distance: {place.get("distance_miles"):.1f} miles</div>'
            
            # Add reviews if available
            if place.get('reviews'):
                html += '<div class="reviews"><strong>Recent Reviews:</strong>'
                for review in place.get('reviews')[:3]:  # Show first 3 reviews
                    review_rating = review.get('rating') or 0
                    review_stars = "⭐" * int(review_rating) if review_rating else ""
                    html += f"""
                    <div class="review">
                        <div class="review-author">{review.get('author_name', 'Anonymous')} 
                        <span class="review-rating">({review.get('rating', 'N/A')} {review_stars})</span></div>
                        <div>"{review.get('text', 'No review text')}"</div>
                        <div style="font-size: 11px; color: #999; margin-top: 5px;">
                            {review.get('time_description', 'Unknown date')}
                        </div>
                    </div>
                    """
                html += '</div>'
            
            html += '</div>'
        
        html += f"""
            <div class="footer">
                <p>This report was generated automatically by the Donation Opportunities Finder system.</p>
                <p>For questions or support, please contact your system administrator.</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_text_report(self, places, search_info):
        """Create a plain text email report"""
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        text = f"""DONATION OPPORTUNITIES FOUND
Generated: {timestamp}

SEARCH DETAILS:
- Search Type: {search_info.get('type', 'Unknown')}
- Location: {search_info.get('location', 'Unknown')}
- Keywords: {search_info.get('keywords', 'N/A')}
- Results Found: {len(places)} organizations

RESULTS:
{'='*60}

"""
        
        for i, place in enumerate(places, 1):
            rating_value = place.get('rating') or 0
            rating_stars = "⭐" * int(rating_value) if rating_value else ""
            rating_text = f"{place.get('rating', 'N/A')} {rating_stars}" if place.get('rating') else "No rating"
            
            text += f"""{i}. {place.get('name', 'Unknown Name')}
   Rating: {rating_text}
   Address: {place.get('address', 'Address not available')}"""
            
            if place.get('phone'):
                text += f"\n   Phone: {place.get('phone')}"
            
            if place.get('email'):
                text += f"\n   Email: {place.get('email')}"
            
            if place.get('website'):
                text += f"\n   Website: {place.get('website')}"
            
            if place.get('distance_miles'):
                text += f"\n   Distance: {place.get('distance_miles'):.1f} miles"
            
            # Add reviews if available
            if place.get('reviews'):
                text += f"\n   Reviews ({len(place.get('reviews'))} total):"
                for review in place.get('reviews')[:2]:  # Show first 2 reviews for text
                    review_rating = review.get('rating') or 0
                    review_stars = "⭐" * int(review_rating) if review_rating else ""
                    text += f"""
     • {review.get('author_name', 'Anonymous')} ({review.get('rating', 'N/A')} {review_stars}):
       "{review.get('text', 'No review text')[:100]}{'...' if len(review.get('text', '')) > 100 else ''}"
       ({review.get('time_description', 'Unknown date')})"""
            
            text += f"\n{'-'*60}\n"
        
        text += """

This report was generated automatically by the Donation Opportunities Finder system.
For questions or support, please contact your system administrator.
"""
        
        return text
    
    def send_results_email(self, places, search_info, attach_files=None):
        """Send email with donation opportunities results using Gmail API"""
        if not self.email_config.get('enabled', True):
            print("📧 Email sending is disabled in configuration")
            return False
        
        recipient = self.email_config.get('recipient')
        if not recipient:
            print("📧 No email recipient configured")
            return False
        
        try:
            # Get Gmail service
            print("📧 Authenticating with Gmail API...")
            service = self._get_gmail_service()
            
            # Use the email from config or a default
            sender_email = self.email_config.get('sender_email', 'cliqueadmin@helpables.org')
            
            # Create subject with search info
            subject_template = self.email_config.get('subject_template', 'Donation Opportunities Found - {search_type}')
            subject = subject_template.format(
                search_type=search_info.get('type', 'Search Results'),
                location=search_info.get('location', ''),
                count=len(places)
            )
            
            # Create both HTML and text versions
            text_content = self._create_text_report(places, search_info)
            html_content = self._create_html_report(places, search_info)
            
            message_content = {
                'text': text_content,
                'html': html_content
            }
            
            # Create message
            sender_name = self.email_config.get('sender', 'Donation Finder System')
            sender_formatted = f"{sender_name} <{sender_email}>"
            
            print(f"📧 Sending email to {recipient}...")
            print(f"   From: {sender_formatted}")
            print(f"   Subject: {subject}")
            
            message = self._create_message(
                sender_formatted, 
                recipient, 
                subject, 
                message_content,
                attach_files
            )
            
            # Send the message
            result = self._send_message(service, 'me', message)
            
            if result:
                print(f"✅ Email sent successfully via Gmail API")
                print(f"   Message ID: {result.get('id', 'Unknown')}")
                print(f"   Results: {len(places)} donation opportunities")
                if attach_files:
                    print(f"   Attachments: {len([f for f in attach_files if os.path.exists(f)])} files")
                return True
            else:
                print("❌ Failed to send email via Gmail API")
                return False
            
        except FileNotFoundError as e:
            print(f"❌ Gmail API setup error: {e}")
            print("\n📝 Gmail API Setup Required:")
            print("   1. Go to Google Cloud Console (console.cloud.google.com)")
            print("   2. Create a new project or select existing one")
            print("   3. Enable Gmail API")
            print("   4. Create OAuth 2.0 credentials")
            print("   5. Download credentials.json file to this directory")
            print("   6. Run the script again to authenticate")
            return False
            
        except ImportError as e:
            print(f"❌ Gmail API dependencies missing: {e}")
            print("📦 Install required packages:")
            print("   pip install google-auth google-auth-oauthlib google-api-python-client")
            return False
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            print("   Please check your Gmail API configuration")
            return False
    
    def is_configured(self):
        """Check if email is properly configured"""
        if not self.email_config.get('enabled', True):
            return False
        
        if not self.email_config.get('recipient'):
            return False
        
        if not GMAIL_API_AVAILABLE:
            return False
        
        # Check if credentials.json exists or if already authenticated
        return os.path.exists('credentials.json') or os.path.exists('token.json')


def test_email_configuration():
    """Test email configuration"""
    sender = EmailSender()
    
    print("📧 Gmail API Email Configuration Test")
    print(f"   Gmail API Available: {'✅ Yes' if GMAIL_API_AVAILABLE else '❌ No'}")
    print(f"   Enabled: {sender.email_config.get('enabled', 'Not set')}")
    print(f"   Recipient: {sender.email_config.get('recipient', 'Not set')}")
    print(f"   Credentials File: {'✅ Found' if os.path.exists('credentials.json') else '❌ Missing'}")
    print(f"   Token File: {'✅ Found' if os.path.exists('token.json') else '❌ Not authenticated yet'}")
    print(f"   Overall Status: {'✅ Ready' if sender.is_configured() else '❌ Not ready'}")
    
    if not sender.is_configured():
        print("\n📝 Gmail API Setup Steps:")
        print("   1. Install dependencies: pip install google-auth google-auth-oauthlib google-api-python-client")
        print("   2. Go to Google Cloud Console (console.cloud.google.com)")
        print("   3. Create/select project and enable Gmail API")
        print("   4. Create OAuth 2.0 credentials (Desktop Application)")
        print("   5. Download credentials.json to this directory")
        print("   6. Set recipient in config.json email_settings")
        print("   7. Run a test email command to authenticate")


if __name__ == '__main__':
    test_email_configuration()