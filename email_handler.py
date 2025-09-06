"""
Email handling module for fetching, parsing, and sending support emails.
"""

import imaplib
import email
import os
from typing import List, Dict, Tuple
from datetime import datetime
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage
from email.utils import parseaddr

# Load environment variables
load_dotenv()


def get_email_counts() -> Tuple[int, int]:
    """
    Get total read and unread email counts for support emails.
    
    Returns:
        Tuple of (unread_count, read_count)
    """
    try:
        gmail_address = os.getenv('GMAIL_ADDRESS')
        gmail_password = os.getenv('GMAIL_PASSWORD')
        
        if not gmail_address or not gmail_password:
            print("Gmail credentials not found in environment variables")
            return 0, 0
        
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(gmail_address, gmail_password)
        mail.select('inbox')
        
        # Search criteria for support emails
        subject_criteria = '(OR (OR (OR SUBJECT "Support" SUBJECT "Query") SUBJECT "Request") SUBJECT "Help")'
        
        # Get unread count
        unread_criteria = f'(UNSEEN {subject_criteria})'
        status, unread_ids = mail.search(None, unread_criteria)
        unread_count = len(unread_ids[0].split()) if status == 'OK' and unread_ids[0] else 0
        
        # Get total count
        status, total_ids = mail.search(None, subject_criteria)
        total_count = len(total_ids[0].split()) if status == 'OK' and total_ids[0] else 0
        
        # Calculate read count
        read_count = total_count - unread_count
        
        mail.close()
        mail.logout()
        
        return unread_count, read_count
        
    except Exception as e:
        print(f"Error getting email counts: {str(e)}")
        return 0, 0


def fetch_support_emails() -> List[Dict[str, str]]:
    """
    Fetch UNREAD support-related emails from Gmail using IMAP.
    
    Returns:
        List of dictionaries containing email data.
    """
    emails = []
    
    try:
        gmail_address = os.getenv('GMAIL_ADDRESS')
        gmail_password = os.getenv('GMAIL_PASSWORD')
        
        if not gmail_address or not gmail_password:
            print("Gmail credentials not found in environment variables")
            return []
        
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(gmail_address, gmail_password)
        mail.select('inbox')
        
        # Search for UNSEEN emails that match our subject keywords
        subject_criteria = '(OR (OR (OR SUBJECT "Support" SUBJECT "Query") SUBJECT "Request") SUBJECT "Help")'
        search_criteria = f'(UNSEEN {subject_criteria})'
        
        status, message_ids = mail.search(None, search_criteria)
        
        if status != 'OK':
            print("Failed to search emails")
            return []
        
        email_ids = message_ids[0].split()[-20:]  # Get last 20 emails
        
        for email_id in email_ids:
            try:
                status, email_data = mail.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    continue
                
                raw_email = email_data[0][1]
                email_message = email.message_from_bytes(raw_email)
                
                sender = email_message.get('From', 'Unknown Sender')
                subject = email_message.get('Subject', 'No Subject')
                date_header = email_message.get('Date', '')
                
                try:
                    if date_header:
                        parsed_date = email.utils.parsedate_tz(date_header)
                        if parsed_date:
                            timestamp = email.utils.mktime_tz(parsed_date)
                            formatted_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
                        else:
                            formatted_date = 'Unknown Date'
                    else:
                        formatted_date = 'Unknown Date'
                except Exception:
                    formatted_date = 'Unknown Date'
                
                body = extract_email_body(email_message)
                
                email_dict = {
                    'id': email_id.decode('utf-8'),
                    'sender': sender,
                    'subject': subject,
                    'date': formatted_date,
                    'body': body
                }
                
                emails.append(email_dict)
                
            except Exception as e:
                print(f"Error processing email {email_id}: {str(e)}")
                continue
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Error connecting to Gmail: {str(e)}")
        return []
    
    return emails


def extract_email_body(email_message: email.message.EmailMessage) -> str:
    """
    Extract text content from email message.
    
    Args:
        email_message: Email message object
        
    Returns:
        Extracted text content
    """
    body = ""
    try:
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    charset = part.get_content_charset() or 'utf-8'
                    body = part.get_payload(decode=True).decode(charset, errors='ignore')
                    break
        else:
            charset = email_message.get_content_charset() or 'utf-8'
            body = email_message.get_payload(decode=True).decode(charset, errors='ignore')
    
    except Exception as e:
        print(f"Error extracting email body: {str(e)}")
        body = "Error extracting email content"
    
    return body.strip()


def send_email(recipient_address: str, subject: str, body: str) -> Tuple[bool, str]:
    """
    Send email response to customer.
    
    Args:
        recipient_address: Email address to send to
        subject: Email subject
        body: Email body content
        
    Returns:
        Tuple of (success, message)
    """
    sender_email = os.getenv('GMAIL_ADDRESS')
    sender_password = os.getenv('GMAIL_PASSWORD')

    if not sender_email or not sender_password:
        return False, "Sender credentials are not configured in the .env file."

    recipient_name, actual_recipient_email = parseaddr(recipient_address)
    
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = f"Re: {subject}"
    msg['From'] = sender_email
    msg['To'] = actual_recipient_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(sender_email, sender_password)
            smtp_server.send_message(msg)
        
        return True, "Email sent successfully!"
    except Exception as e:
        print(f"Error sending email: {e}")
        return False, f"Failed to send email. Error: {e}"