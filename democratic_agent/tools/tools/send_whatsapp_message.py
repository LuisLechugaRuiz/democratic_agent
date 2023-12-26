import pywhatkit

# Limitation: install from source, current pip is broken.


def send_whatsapp_message(phone_number: str, message: str):
    """Send WhatsApp Message to a Contact Instantly

    Args:
        phone_number (str): The phone number of the contact, should contain the country code.
        message (str): The message to be sent to the contact.
    """
    try:
        pywhatkit.sendwhatmsg_instantly(phone_number, message)
        return "Message sent successfully!"
    except Exception as e:
        return f"Failed with error: {e}"


def main():
    send_whatsapp_message("+351912345678", "Hello World!")


if __name__ == "__main__":
    main()
