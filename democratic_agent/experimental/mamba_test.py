import os
import traceback
from transformers import AutoTokenizer, TextStreamer
import torch

# Model specific
from mamba_ssm.models.mixer_seq_simple import MambaLMHeadModel

# Utils
from utils.helpers import colored


def load_or_download_model(model_type, model_name, device="cuda"):
    local_model_name = model_name.replace("/", "_")
    local_model_path = f"models/{local_model_name}"

    def _load_model(model_path):
        # Using dtype instead of torch_dtype and device instead of device_map, TODO: Verify to generalize it.
        return model_type.from_pretrained(
            model_path,
            dtype=torch.bfloat16,
            device=device
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
    # TODO: Make this automatic, load from config file.
    model_type = MambaLMHeadModel
    device = "cuda"
    is_finetuned = True  # TODO: get from args

    if is_finetuned:
        tokenizer_model = "Schmadge/mamba-slim-orca" # "EleutherAI/gpt-neox-20b"
        model_name = "Schmadge/mamba-slim-orca"
    else:
        tokenizer_model = "EleutherAI/gpt-neox-20b"
        model_name = "state-spaces/mamba-2.8b"

    # Initialization
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_model)
    if is_finetuned:
        tokenizer.chat_template = AutoTokenizer.from_pretrained("HuggingFaceH4/zephyr-7b-beta").chat_template
        tokenizer.eos_token = tokenizer.pad_token = "<|endoftext|>"  # TODO: Move to cfg

    model = load_or_download_model(model_type, model_name)
    streamer = TextStreamer(tokenizer, skip_prompt=True)

    system_prompt = "You are an AI assistant. Provide a detailed answer so user don't need to search outside to understand the answer."

    # Looks like model is not trained to produce eos...
    max_length = 2048

    # Generation
    while True:
        # Get user input
        user_prompt = input("Enter prompt: ")

        # Preparing the prompt
        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        input_ids = tokenizer.apply_chat_template(prompt, return_tensors="pt", add_generation_prompt=True).to(device)

        # Model response
        try:
            out = model.generate(
                input_ids=input_ids,
                max_length=max_length,
                temperature=1.0,
                cg=True,
                top_k=1,
                top_p=1.0,
                streamer=streamer,
                eos_token_id=tokenizer.eos_token_id,
            )
            decoded = tokenizer.batch_decode(out)

            response = decoded[0].split("<|assistant|>\n")[-1].replace('<|endoftext|>','')
            # Save tokens in history vs try to hold the current mamba imp.
        except Exception as e:
            traceback.print_exc()  # Print detailed traceback
            print(colored(f"FAILED! Exception: {e}", "red"))


if __name__ == "__main__":
    main()
