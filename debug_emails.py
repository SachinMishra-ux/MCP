import os
import sys
sys.path.append('email-copilot')
import oauth_manager
import imaplib
import email
from email.header import decode_header

def debug_inbox():
    email_user = 'sachin319566@gmail.com'
    os.environ['EMAIL_USER'] = email_user
    
    creds = oauth_manager.load_credentials()
    if not creds:
        print("Failed to load credentials")
        return

    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        auth_string = oauth_manager.get_auth_string(email_user, creds.token)
        mail.authenticate('XOAUTH2', lambda x: auth_string)
        
        mail.select('inbox')
        
        # 1. Total Unread
        status, messages = mail.search(None, 'UNSEEN')
        ids = messages[0].split()
        print(f"Total Unread Count: {len(ids)}")
        
        print("\nLast 20 Unread Subjects:")
        for num in ids[-20:]:
            res, data = mail.fetch(num, '(BODY.PEEK[HEADER.FIELDS (SUBJECT)])')
            msg = email.message_from_bytes(data[0][1])
            subject, encoding = decode_header(msg['Subject'])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else 'utf-8')
            print(f"- {num.decode()}: {subject}")

        # 2. Search for "Job Opportunity" specifically
        print("\nSearching for 'Job Opportunity' specifically...")
        # Try raw search for better results on Gmail
        status, search_res = mail.search(None, 'SUBJECT "Job Opportunity"')
        search_ids = search_res[0].split()
        print(f"Search 'SUBJECT \"Job Opportunity\"' Results: {len(search_ids)}")
        for num in search_ids:
             print(f"- Match ID: {num.decode()}")

        status, search_res_raw = mail.search(None, 'X-GM-RAW "Job Opportunity"')
        search_ids_raw = search_res_raw[0].split()
        print(f"Search 'X-GM-RAW \"Job Opportunity\"' Results: {len(search_ids_raw)}")
        for num in search_ids_raw:
             print(f"- Match ID (RAW): {num.decode()}")
             
        mail.logout()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_inbox()
