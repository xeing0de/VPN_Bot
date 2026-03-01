import json

def get_data(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data

def save_data(path: str, info: dict) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(info, file, ensure_ascii=False, indent=2)
