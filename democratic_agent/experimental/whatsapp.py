# Importing the Required Library

# Limitations:
# - Runs pyautogui and open the web...
# - Needs phone instead of contact name...
# - Needs group link instead of group name....
# - Random log txt saved
# - Last pip version fails... due to the failure of new release (check -> https://pypi.org/project/pywhatkit/5.4.1/)... might need to install from source or help to make the release.
import pywhatkit


def send_message_to_group(group_id: str, message: str):
    """Send WhatsApp Message to a Group Instantly"""
    pywhatkit.sendwhatmsg_to_group_instantly(group_id, message)


def send_message_to_contact(phone_number: str, message: str):
    """Send WhatsApp Message to a Contact Instantly"""
    pywhatkit.sendwhatmsg_instantly(phone_number, message, wait_time=30)


def main():
    # number = input("Number: ")
    # country_code = input("Country code: ")
    # message = input("Message: ")
    # number = country_code + number
    # send_message_to_contact(number, message)
    # send_message_to_group(
    #    "xxxx",
    #    "Test",
    # )
    pass


if __name__ == "__main__":
    main()
