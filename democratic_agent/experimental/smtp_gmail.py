import smtplib
from email.mime.text import MIMEText


def send_email(smtp_server, port, username, password, recipient, subject, body):
    # Create MIMEText object for the email body
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = username
    message["To"] = recipient

    # Connect to the SMTP server and send the email
    try:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(username, password)
            server.send_message(message)
            print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")


# User inputs
smtp_server = "smtp.gmail.com"
port = 587

recipient = input("Enter the recipient's email address: ")
username = input("Enter your email address: ")
password = input("Enter your email password: ")
subject = "Test smtp email"
body = "Test test."

send_email(smtp_server, port, username, password, recipient, subject, body)
