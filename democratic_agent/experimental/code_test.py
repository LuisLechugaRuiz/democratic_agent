import traceback
from io import StringIO
from contextlib import redirect_stdout
import re
from transformers import AutoTokenizer, LlamaForCausalLM, TextStreamer
import torch

# from optimum.nvidia import LlamaForCausalLM -> TODO: Enable

# TODO: move to utils.
from utils.helpers import colored

MAGICODER_PROMPT = """You are an exceptionally intelligent coding assistant that consistently delivers accurate and reliable responses to user instructions. Always write Python code to answer questions, keep the code as short as possible.

@@ Instruction
{instruction}

@@ Response
"""


local_model_path = "models/ise-uiuc_Magicoder-S-DS-6.7B"
model = LlamaForCausalLM.from_pretrained(
    local_model_path, torch_dtype=torch.bfloat16, device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(local_model_path)
streamer = TextStreamer(tokenizer, skip_prompt=True)

while 1:
    # Get user input
    instruction = input("Enter instruction: ")
    prompt = MAGICODER_PROMPT.format(instruction=instruction)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    # Model response
    try:
        tokens = model.generate(
            **inputs,
            max_length=4096,
            num_return_sequences=1,
            temperature=0.0,
            streamer=streamer,
        )
        new_output = tokenizer.decode(tokens[0], skip_special_tokens=True)
        print("DEBUG - new_output:", new_output)
    except Exception as e:
        print(colored(f"FAILED! Exception: {e}", "red"))
        continue

    pattern = r"```python\n(.*?)```"
    matches = re.findall(pattern, new_output, re.DOTALL)
    for python_code in matches:
        # AI safety. Warning to user. Do not press y if the AI is trying to do unsafe things.
        if input(colored("<-- PYTHON DETECTED, RUN IT? ", "red")).lower() == "y":
            my_stdout = StringIO()
            try:
                with redirect_stdout(my_stdout):
                    exec(python_code)
                result = my_stdout.getvalue()
            except Exception as e:
                result = "".join(traceback.format_exception_only(e))
            print(colored(f"Result:\n{result}", "green"))
        if input(colored("<-- SAVE PYTHON CODE? ", "red")).lower() == "y":
            name = input(colored("<-- NAME OF FILE? ", "red"))
            with open(f"generated_code/{name}.py", "w") as f:
                f.write(python_code)
