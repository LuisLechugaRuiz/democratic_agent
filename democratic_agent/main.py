import subprocess
import signal
from dotenv import load_dotenv

import democratic_agent.architecture.user.user as user_module
import democratic_agent.architecture.system.system as system_module

# import os
# import tensorflow as tf

# os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Suppress TensorFlow logs
# tf.get_logger().setLevel("ERROR")


def terminate_tmux_panes(session_name):
    # Terminate processes in tmux panes
    subprocess.run(["tmux", "send-keys", "-t", f"{session_name}:0.0", "C-c", "C-m"])
    subprocess.run(["tmux", "send-keys", "-t", f"{session_name}:0.1", "C-c", "C-m"])
    subprocess.run(["tmux", "kill-session", "-t", session_name])


def signal_handler(sig, frame):
    print("Ctrl+C pressed, terminating processes...")
    terminate_tmux_panes("mysession")
    exit(0)


def main():
    load_dotenv()

    signal.signal(signal.SIGINT, signal_handler)

    # Run the scripts in separate tmux panes
    system_file = f"python3 {system_module.__file__}"
    user_file = f"python3 {user_module.__file__}"

    subprocess.run(["tmux", "new-session", "-d", "-s", "mysession"])
    subprocess.run(["tmux", "split-window", "-h"])
    subprocess.run(["tmux", "send-keys", "-t", "mysession:0.0", system_file, "C-m"])
    subprocess.run(["tmux", "send-keys", "-t", "mysession:0.1", user_file, "C-m"])
    subprocess.run(["tmux", "attach-session", "-t", "mysession"])


if __name__ == "__main__":
    main()
