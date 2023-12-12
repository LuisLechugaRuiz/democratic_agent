import traceback
import os

from democratic_agent.utils.helpers import colored
from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer


def load_or_download_model(model_type, model_name, device="cuda"):
    local_model_name = model_name.replace("/", "_")
    local_model_path = f"models/{local_model_name}"

    def _load_model(model_path):
        # Using dtype instead of torch_dtype and device instead of device_map, TODO: Verify to generalize it.
        return model_type.from_pretrained(
            model_path,
            device_map="auto",
            trust_remote_code=False,
            revision="gptq-3bit-128g-actorder_True",
        )

    # Check if the local model directory exists
    if not os.path.exists(local_model_path):
        # If the model directory does not exist, download the model from Hugging Face
        print(f"Model not found locally. Downloading from Hugging Face: {model_name}")
        model = _load_model(model_name)
        # Save the model locally for future use
        model.save_pretrained(local_model_path)
    else:
        # If the model directory exists, load the model from the local directory
        print(f"Loading model from local path: {local_model_path}")
        model = _load_model(local_model_path)
    return model


def main():
    model_name_or_path = "TheBloke/una-xaberius-34b-v1beta-GPTQ"
    # TODO: Make this automatic, load from config file.
    model_type = AutoModelForCausalLM

    # Initialization
    tokenizer = AutoTokenizer.from_pretrained(
        model_name_or_path, use_fast=True, device_map="auto"
    )

    model = load_or_download_model(model_type, model_name_or_path)
    streamer = TextStreamer(tokenizer, skip_prompt=True)

    prompt_template = """<|im_start|>system
- You are a helpful assistant chatbot trained by MosaicML.
- You answer questions.
- You are excited to be able to help the user, but will refuse to do anything that could be considered harmful to the user.
- You are more than just an information source, you are also able to write poetry, short stories, and make jokes.<|im_end|>
<|im_start|>user
{prompt}<|im_end|>
<|im_start|>assistant"""

    # Generation
    while True:
        # Get user input
        user_prompt = input("Enter prompt: ")
        prompt = prompt_template.format(prompt=user_prompt)

        # Model response
        try:
            input_ids = tokenizer(prompt, return_tensors="pt").input_ids
            output = model.generate(
                inputs=input_ids,
                temperature=0.7,
                do_sample=True,
                top_p=0.95,
                top_k=40,
                max_new_tokens=512,
                streamer=streamer,
            )
            decoded = tokenizer.decode(output[0])
            # Save tokens in history vs try to hold the current mamba imp.
        except Exception as e:
            traceback.print_exc()  # Print detailed traceback
            print(colored(f"FAILED! Exception: {e}", "red"))


if __name__ == "__main__":
    main()
