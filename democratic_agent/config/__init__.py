from pathlib import Path
import yaml


def get_modules():
    modules_path = Path(__file__).parent / "modules.yaml"
    return yaml.safe_load(open(modules_path))
