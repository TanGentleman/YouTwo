import json
from pathlib import Path

def save_dict_to_file(data: dict, filepath: str):
    """
    Saves the data to a JSON file.
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)