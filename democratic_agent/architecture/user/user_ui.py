# TODO: Use a proper ui, probably the next version of https://github.com/mckaywrigley/chatbot-ui.
import argparse
import curses
import time
import random

from democratic_agent.architecture.helpers.tmp_ips import (
    DEF_ASSISTANT_IP,
)
from democratic_agent.architecture.user.user import User


class UserUI:
    def __init__(self, user: User):
        self.user = user
        self.num_colors = self.init_colors()  # Initialize colors and get the count
        self.user_colors = {"Aware": 1}  # Maps usernames to color pair numbers
        self.available_colors = list(
            range(2, self.num_colors + 1)
        )  # List of available color pair numbers

    def chat_ui(self, stdscr):
        # Setup windows for chat history and message input
        curses.cbreak()
        stdscr.nodelay(True)
        height, width = stdscr.getmaxyx()
        chat_win = curses.newwin(height - 3, width, 0, 0)
        chat_win.scrollok(True)
        input_win = curses.newwin(3, width, height - 3, 0)
        input_buffer = ""

        last_displayed_msg_index = 0  # Index of the last displayed message

        while True:
            # Only update if there are new messages
            if last_displayed_msg_index < len(self.user.incoming_messages):
                new_messages = self.user.incoming_messages[last_displayed_msg_index:]
                for msg in new_messages:
                    color_pair_number = self.get_user_color(msg.user_name)
                    # Add the username with color
                    chat_win.addstr(
                        f"{msg.user_name}", curses.color_pair(color_pair_number)
                    )
                    # Add the rest of the message in the default color
                    chat_win.addstr(f": {msg.message}\n\n")
                last_displayed_msg_index = len(self.user.incoming_messages)

            chat_win.refresh()

            # Check for new input
            try:
                char = stdscr.getkey()
                if char == "\n":
                    # Enter pressed, send message
                    self.user.send_message(input_buffer)
                    input_buffer = ""
                elif char == "\x1b":  # Escape key
                    break
                elif char in [
                    "\x08",
                    "\x7f",
                    "KEY_BACKSPACE",
                ]:  # Backspace or delete key
                    input_buffer = input_buffer[:-1]  # Remove last character
                else:
                    input_buffer += char
            except curses.error:
                # No input
                pass

            # Display input buffer
            input_win.clear()
            input_win.addstr("Enter message: " + input_buffer)
            input_win.refresh()

            time.sleep(0.1)  # Small delay to reduce CPU usage

    def init_colors(self):
        curses.start_color()
        color_pairs = [
            (curses.COLOR_BLUE, curses.COLOR_BLACK),
            (curses.COLOR_RED, curses.COLOR_BLACK),
            (curses.COLOR_GREEN, curses.COLOR_BLACK),
            (curses.COLOR_YELLOW, curses.COLOR_BLACK),
            (curses.COLOR_MAGENTA, curses.COLOR_BLACK),
            (curses.COLOR_CYAN, curses.COLOR_BLACK),
            (curses.COLOR_WHITE, curses.COLOR_BLACK),
        ]

        for i, (fg, bg) in enumerate(color_pairs, start=1):
            curses.init_pair(i, fg, bg)

        return len(color_pairs)  # Return the number of color pairs initialized

    def get_user_color(self, user_name):
        # If the user already has a color pair number, return it
        if user_name in self.user_colors:
            return self.user_colors[user_name]

        # If all colors are used, reset the available colors list
        if not self.available_colors:
            self.available_colors = list(range(2, self.num_colors + 1))

        # Assign a random color pair number from the available colors
        chosen_color_pair_number = random.choice(self.available_colors)
        self.available_colors.remove(chosen_color_pair_number)
        self.user_colors[user_name] = chosen_color_pair_number

        return chosen_color_pair_number


def main(stdscr):
    parser = argparse.ArgumentParser(description="User configuration script.")
    parser.add_argument("-n", "--name", default="Luis", help="User name")
    parser.add_argument(
        "-a",
        "--assistant_ip",
        type=str,
        default=DEF_ASSISTANT_IP,
        help="Assistant IP",
    )
    args = parser.parse_args()

    # Initialize user and user UI
    user = User(
        args.name,
        assistant_ip=args.assistant_ip,
    )
    ui = UserUI(user=user)
    ui.chat_ui(stdscr)  # Start the chat UI


# Ensure curses wrapper is used to start the main function
if __name__ == "__main__":
    curses.wrapper(main)
