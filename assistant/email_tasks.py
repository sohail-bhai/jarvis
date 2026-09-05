import imaplib
import email
from email.header import decode_header
from assistant.config import get_setting

def read_unread_emails(limit=5):
    """Connects to Gmail via IMAP and reads unread emails."""
    email_address = get_setting("email_address")
    app_password = get_setting("email_app_password")

    if not email_address or not app_password:
        return "Email credentials not configured. Please ask the user to add email_address and email_app_password to config.json."

    if app_password.startswith("secret://"):
        try:
            from assistant.control.store import ControlStore
            from assistant.control.secrets import SecretStore, load_key
            store = ControlStore()
            secrets = SecretStore(store, key=load_key())
            app_password = secrets.resolve(app_password)
        except Exception as e:
            return f"Could not resolve secret for email password: {e}"

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_address, app_password)
        mail.select("inbox")

        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            return "Failed to search for emails."

        email_ids = messages[0].split()
        if not email_ids:
            return "You have no unread emails."

        # Grab the latest N emails
        latest_ids = email_ids[-limit:]
        
        results = []
        for e_id in latest_ids:
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Decode subject
                    subject, encoding = decode_header(msg.get("Subject", "No Subject"))[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    
                    # Decode From
                    from_header, encoding = decode_header(msg.get("From", "Unknown"))[0]
                    if isinstance(from_header, bytes):
                        from_header = from_header.decode(encoding if encoding else "utf-8")
                        
                    results.append(f"From: {from_header}\nSubject: {subject}")
                    
        mail.logout()
        
        summary = "\n\n".join(results)
        return f"Found {len(latest_ids)} unread emails:\n\n{summary}"

    except Exception as e:
        return f"Error reading emails: {e}"

import smtplib
from email.message import EmailMessage

def send_email(to_address, subject, body):
    """Connects to Gmail via SMTP and sends an email."""
    email_address = get_setting("email_address")
    app_password = get_setting("email_app_password")

    if not email_address or not app_password:
        return "Email credentials not configured in config.json."

    if app_password.startswith("secret://"):
        try:
            from assistant.control.store import ControlStore
            from assistant.control.secrets import SecretStore, load_key
            store = ControlStore()
            secrets = SecretStore(store, key=load_key())
            app_password = secrets.resolve(app_password)
        except Exception as e:
            return f"Could not resolve secret for email password: {e}"

    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = email_address
        msg["To"] = to_address

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_address, app_password)
            server.send_message(msg)
            
        return f"Successfully sent email to {to_address}"
    except Exception as e:
        return f"Error sending email: {e}"
