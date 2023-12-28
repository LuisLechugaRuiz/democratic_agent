import imaplib
import email
import email.header
from email.header import decode_header


def fetch_emails(username, password, server, port, folder):
    # Connect to the server
    mail = imaplib.IMAP4_SSL(server, port)
    mail.login(username, password)

    # Select the folder
    mail.select(folder)

    # Fetch the emails
    result, data = mail.search(None, "ALL")
    mail_ids = data[0]
    id_list = mail_ids.split()

    for num in data[0].split():
        typ, data = mail.fetch(num, "(RFC822)")
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)

        # Decode the subject
        subject, encoding = decode_header(email_message["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding)

        # Decode the body
        body = ""
        if email_message.is_multipart():
            for part in email_message.get_payload():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload()
                    break
        else:
            body = email_message.get_payload()

        # Save the email to a file
        with open(f"{subject}.txt", "w") as file:
            file.write(f"Subject: {subject}\n\n")
            file.write(body)

    # Close the connection
    mail.close()
    mail.logout()


# Replace the following with your actual credentials and server details
fetch_emails("xxxx", "yyyy", "imap.gmail.com", 993, "INBOX")
